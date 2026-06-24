"""
Unit tests for create_mock_exam and evaluate_answer MCP tools.

These tests mock the Anthropic API client to verify:
  - create_mock_exam generates a properly structured exam
  - evaluate_answer grades answers and returns feedback
  - The tool dispatcher routes both new tools correctly
  - Edge cases (empty answers, malformed responses) are handled

Run with: pytest tests/test_mock_exam.py -v
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.mcp_servers.exam_prep_server import (
    EXAM_PREP_TOOLS,
    create_mock_exam,
    evaluate_answer,
    execute_tool,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_model_env(monkeypatch):
    """Ensure a consistent model name is used during tests."""
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-4-5")


# ---------------------------------------------------------------------------
# create_mock_exam tests
# ---------------------------------------------------------------------------

class TestCreateMockExam:
    """Tests for the create_mock_exam MCP tool."""

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_generates_structured_exam(self, mock_client):
        """A valid Claude response should be parsed into a structured exam dict."""
        mock_client.messages.create.return_value = _make_response({
            "title": "Machine Learning Fundamentals — Mock Exam",
            "topic": "machine learning basics",
            "difficulty": "medium",
            "duration_minutes": 60,
            "time_per_question_minutes": 3,
            "instructions": "Answer all questions. Each question is worth 5 points.",
            "total_questions": 2,
            "questions": [
                {
                    "number": 1,
                    "question": "What is overfitting?",
                    "options": {
                        "A": "When a model performs well on training data but poorly on new data",
                        "B": "When a model performs poorly on all data",
                        "C": "When a model has too few parameters",
                        "D": "When training takes too long",
                    },
                    "correct_answer": "A",
                    "explanation": "Overfitting occurs when a model learns the training data too well.",
                    "topic_tag": "model generalization",
                },
                {
                    "number": 2,
                    "question": "Which algorithm is used for classification?",
                    "options": {
                        "A": "K-Means",
                        "B": "Linear Regression",
                        "C": "Logistic Regression",
                        "D": "PCA",
                    },
                    "correct_answer": "C",
                    "explanation": "Logistic Regression is a classification algorithm despite its name.",
                    "topic_tag": "classification algorithms",
                },
            ],
        })

        result = create_mock_exam(
            topic="machine learning basics",
            num_questions=2,
            difficulty="medium",
            duration_minutes=60,
        )

        assert result["status"] == "ok"
        assert result["title"] == "Machine Learning Fundamentals — Mock Exam"
        assert result["difficulty"] == "medium"
        assert result["duration_minutes"] == 60
        assert result["total_questions"] == 2
        assert result["rag_enriched"] is False
        assert len(result["questions"]) == 2
        # Verify question structure
        q1 = result["questions"][0]
        assert q1["number"] == 1
        assert "options" in q1
        assert "correct_answer" in q1
        assert "explanation" in q1
        assert "topic_tag" in q1

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_rag_enriched_when_collection_provided(self, mock_client):
        """When collection_name is given, rag_enriched should be True."""
        mock_client.messages.create.return_value = _make_response({
            "title": "RAG-based Exam",
            "topic": "test",
            "difficulty": "easy",
            "duration_minutes": 30,
            "time_per_question_minutes": 6,
            "instructions": "Test exam.",
            "total_questions": 1,
            "questions": [
                {
                    "number": 1,
                    "question": "What is 2+2?",
                    "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
                    "correct_answer": "B",
                    "explanation": "Basic arithmetic.",
                    "topic_tag": "math",
                },
            ],
        })

        with patch("backend.mcp_servers.exam_prep_server.search_documents") as mock_search:
            mock_search.return_value = [
                {"page": 1, "source": "test.pdf", "text": "Some context", "score": 0.9}
            ]
            result = create_mock_exam(
                topic="test topic",
                collection_name="test_collection",
                num_questions=1,
            )

        assert result["rag_enriched"] is True
        mock_search.assert_called_once()

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_strips_code_fences(self, mock_client):
        """Claude sometimes wraps JSON in markdown code fences — we strip them."""
        raw = '```json\n' + json.dumps({
            "title": "Fenced Exam",
            "topic": "test",
            "difficulty": "easy",
            "duration_minutes": 30,
            "time_per_question_minutes": 6,
            "instructions": "Test.",
            "total_questions": 1,
            "questions": [
                {
                    "number": 1,
                    "question": "Q?",
                    "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "correct_answer": "A",
                    "explanation": "Because.",
                    "topic_tag": "test",
                },
            ],
        }) + '\n```'
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=raw)]
        )

        result = create_mock_exam(topic="anything", num_questions=1)
        assert result["status"] == "ok"
        assert result["title"] == "Fenced Exam"

    def test_tool_definition_in_registry(self):
        """create_mock_exam must appear in EXAM_PREP_TOOLS."""
        names = [t["name"] for t in EXAM_PREP_TOOLS]
        assert "create_mock_exam" in names

    def test_dispatcher_routes_to_function(self):
        """execute_tool must route 'create_mock_exam' to the right function."""
        with patch("backend.mcp_servers.exam_prep_server.create_mock_exam") as mock_fn:
            mock_fn.return_value = {"status": "ok", "title": "Test"}
            result = execute_tool("create_mock_exam", {"topic": "test"})
            mock_fn.assert_called_once_with(topic="test")
            assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# evaluate_answer tests
# ---------------------------------------------------------------------------

class TestEvaluateAnswer:
    """Tests for the evaluate_answer MCP tool."""

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_correct_answer_gets_high_score(self, mock_client):
        """An exactly correct answer should score 90-100."""
        mock_client.messages.create.return_value = _make_response({
            "is_correct": True,
            "score": 95,
            "correctness_label": "exactly_correct",
            "feedback": "Perfect! You clearly understand the concept.",
            "what_the_student_got_right": "You identified the key principle correctly.",
            "what_to_improve": "Nothing — solid understanding.",
            "key_concept": "neural network backpropagation",
        })

        result = evaluate_answer(
            question="What does backpropagation do?",
            student_answer="It calculates gradients to update weights during training.",
            correct_answer="It computes gradients of the loss with respect to weights.",
        )

        assert result["status"] == "ok"
        assert result["is_correct"] is True
        assert result["score"] == 95
        assert result["correctness_label"] == "exactly_correct"
        assert "feedback" in result
        assert "what_the_student_got_right" in result
        assert "what_to_improve" in result
        assert "key_concept" in result

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_incorrect_answer_gets_low_score(self, mock_client):
        """A wrong answer should score below 40 and flag as incorrect."""
        mock_client.messages.create.return_value = _make_response({
            "is_correct": False,
            "score": 20,
            "correctness_label": "incorrect",
            "feedback": "This answer confuses backpropagation with forward propagation.",
            "what_the_student_got_right": "You mentioned weights, which is relevant.",
            "what_to_improve": "Study the difference between forward and backward passes.",
            "key_concept": "backpropagation algorithm",
        })

        result = evaluate_answer(
            question="What does backpropagation do?",
            student_answer="It makes predictions on input data.",
            correct_answer="It computes gradients to update weights.",
            explanation="Backpropagation uses the chain rule to compute gradients.",
        )

        assert result["status"] == "ok"
        assert result["is_correct"] is False
        assert result["score"] == 20
        assert result["correctness_label"] == "incorrect"
        assert "question_preview" in result

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_explanation_passed_to_prompt(self, mock_client):
        """When explanation is provided, it should be included in the grading prompt."""
        mock_client.messages.create.return_value = _make_response({
            "is_correct": True,
            "score": 100,
            "correctness_label": "exactly_correct",
            "feedback": "Great!",
            "what_the_student_got_right": "Everything.",
            "what_to_improve": "Nothing.",
            "key_concept": "test",
        })

        evaluate_answer(
            question="Q?",
            student_answer="A",
            correct_answer="A",
            explanation="Because A is correct.",
        )

        # Check the prompt sent to Claude contains the explanation
        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "Because A is correct." in prompt

    def test_tool_definition_in_registry(self):
        """evaluate_answer must appear in EXAM_PREP_TOOLS."""
        names = [t["name"] for t in EXAM_PREP_TOOLS]
        assert "evaluate_answer" in names

    def test_dispatcher_routes_to_function(self):
        """execute_tool must route 'evaluate_answer' to the right function."""
        with patch("backend.mcp_servers.exam_prep_server.evaluate_answer") as mock_fn:
            mock_fn.return_value = {"status": "ok", "score": 80}
            result = execute_tool(
                "evaluate_answer",
                {
                    "question": "Q?",
                    "student_answer": "A",
                    "correct_answer": "B",
                },
            )
            mock_fn.assert_called_once_with(
                question="Q?",
                student_answer="A",
                correct_answer="B",
            )
            assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases for both new tools."""

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_evaluate_answer_with_empty_student_answer(self, mock_client):
        """An empty answer should still be graded (handled by Claude)."""
        mock_client.messages.create.return_value = _make_response({
            "is_correct": False,
            "score": 0,
            "correctness_label": "incorrect",
            "feedback": "No answer provided.",
            "what_the_student_got_right": "Nothing — answer was empty.",
            "what_to_improve": "Please provide an answer.",
            "key_concept": "test",
        })

        result = evaluate_answer(
            question="What is 2+2?",
            student_answer="",
            correct_answer="4",
        )
        assert result["status"] == "ok"
        assert result["is_correct"] is False

    @patch("backend.mcp_servers.exam_prep_server._client")
    def test_create_mock_exam_minimum_questions(self, mock_client):
        """Should work with the minimum of 1 question."""
        mock_client.messages.create.return_value = _make_response({
            "title": "Minimal Exam",
            "topic": "test",
            "difficulty": "easy",
            "duration_minutes": 10,
            "time_per_question_minutes": 10,
            "instructions": "One question only.",
            "total_questions": 1,
            "questions": [
                {
                    "number": 1,
                    "question": "Q?",
                    "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "correct_answer": "A",
                    "explanation": "A is correct.",
                    "topic_tag": "minimal",
                },
            ],
        })

        result = create_mock_exam(topic="test", num_questions=1, duration_minutes=10)
        assert result["total_questions"] == 1
        assert result["time_per_question_minutes"] == 10

    def test_dispatcher_raises_on_unknown_tool(self):
        """execute_tool should raise ValueError for unknown tool names."""
        with pytest.raises(ValueError, match="Unknown tool: not_a_real_tool"):
            execute_tool("not_a_real_tool", {})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(data: dict) -> MagicMock:
    """Build a mocked Anthropic API response whose .content[0].text is JSON."""
    return MagicMock(content=[MagicMock(text=json.dumps(data))])
