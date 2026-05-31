# SAGE — Agentic AI Student Assistant

**SAGE (Student Academic Guidance Engine) is an intelligent, agentic multi-tool platform that helps university students prepare for exams, navigate course decisions, and automate academic logistics - powered by Claude, the Model Context Protocol (MCP), and Retrieval-Augmented Generation (RAG).**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Claude-Anthropic-D97757?logo=anthropic&logoColor=white" alt="Claude">
  <img src="https://img.shields.io/badge/MCP-Model_Context_Protocol-8B5CF6" alt="MCP">
  <img src="https://img.shields.io/badge/RAG-LlamaIndex_+_ChromaDB-22D3EE" alt="RAG">
  <img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-GPL--3.0-green" alt="License">
</p>

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Why This Architecture](#why-this-architecture)
4. [System Architecture](#system-architecture)
5. [Technology Stack](#technology-stack)
6. [Project Phases](#project-phases)
7. [MCP Tool Servers](#mcp-tool-servers)
8. [Project Structure](#project-structure)
9. [Installation and Setup](#installation-and-setup)
10. [Configuration](#configuration)
11. [Running the Application](#running-the-application)
12. [Usage Examples](#usage-examples)
13. [Roadmap](#roadmap)
14. [Team](#team)
15. [Contributing](#contributing)
16. [Contact](#contact)

---

## Project Overview

**SAGE** is an agentic AI assistant designed to support the full academic journey of a
university student. Rather than being a single chatbot, it is an **orchestrated system
of specialized tools** that Claude (Anthropic's LLM) calls autonomously based on what
the student needs.

A student logs in, uploads their own course materials (PDFs, lecture slides, notes),
and chats naturally with the assistant. Behind the scenes, Claude decides *which tool
to invoke* — generating a quiz from the uploaded material, answering a question grounded
in the student's documents, building a revision schedule, or recommending a course.

The platform showcases three of the most important technologies in modern applied AI:

- **MCP (Model Context Protocol)** — a standardized protocol for exposing tools to
  an LLM, allowing Claude to discover and call functions autonomously.
- **RAG (Retrieval-Augmented Generation)** — grounding the LLM's answers in the
  student's actual documents using semantic search, eliminating hallucination.
- **Agentic Tool-Use** — Claude reasons about the student's intent and orchestrates
  multiple tools to fulfil complex requests, without hard-coded routing logic.

---

## Key Features

- **Document-Grounded Q&A** — Upload your lecture notes and ask questions answered
  directly from *your* material, with source citations (RAG).
- **Adaptive Quiz Generation** — Generate quizzes on any topic from your uploaded
  documents, with adjustable difficulty.
- **Weakness Detection** — The system tracks which topics you struggle with and
  prioritizes them in future revision.
- **Smart Revision Plans** — Generate buffer-aware, time-boxed study schedules that
  adapt to your confidence levels and exam dates.
- **Mock Exam Simulation** — Take realistic, timed practice exams with automated
  grading and feedback.
- **University GPT Chatbot** — Ask questions about university policies, course
  catalogs, and procedures (RAG over institutional documents).
- **Course Advising** — Get course recommendations based on your interests and
  academic progress.
- **Campus Automation** — Parse timetables, track deadlines, and receive reminders.

---

## Why This Architecture

A common approach to agentic systems is to build a heavy orchestration layer (for
example, a custom "coordinator agent" with a state machine) that routes requests to
sub-agents. We deliberately chose a **leaner, MCP-first design**:

> **Claude is the orchestrator.** We expose well-designed tools through MCP, and the
> model reasons about which tools to call. This removes thousands of lines of routing
> logic while producing genuinely autonomous, agentic behaviour.

This decision makes the system **easier to maintain**, **cheaper to run** (fewer LLM
calls), and **forward-compatible** — the MCP tool servers we build could later be
exposed to other MCP clients such as Claude Desktop or IDEs.

---

## System Architecture

```
+----------------------------------------------------------+
|              STREAMLIT FRONTEND (pure Python)            |
|          Chat - Upload - Quiz - Tasks - Dashboard        |
+----------------------------+-----------------------------+
                             | HTTP
+----------------------------v-----------------------------+
|                     FASTAPI BACKEND                      |
|          /auth - /chat - /upload - /quiz - /tasks        |
+----------------------------+-----------------------------+
                             |
+----------------------------v-----------------------------+
|                 ASSISTANT CLIENT (the brain)             |
|     Loads history -> calls Claude with MCP tools ->      |
|         executes tool calls -> returns response          |
+----------+-------------------+-------------------+-------+
           | MCP               | MCP               | MCP
+----------v-------+ +---------v--------+ +--------v--------+
|    EXAM PREP     | |     ADVISOR      | |     CAMPUS      |
|     SERVER       | |     SERVER       | |     SERVER      |
+----------+-------+ +---------+--------+ +--------+--------+
           |                   |                   |
+----------v-------------------v-------------------v-------+
|                     SHARED FOUNDATION                    |
|             RAG engine (LlamaIndex + ChromaDB)           |
|              Database (SQLite / SQLAlchemy)              |
|                   Claude client wrapper                  |
+----------------------------------------------------------+
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.12 | Core implementation language |
| Backend | FastAPI | Async REST API with auto-generated docs |
| LLM | Claude (Anthropic) | Reasoning, generation, and tool orchestration |
| Tool Protocol | MCP (Model Context Protocol) | Standardized tool exposure to the LLM |
| RAG Framework | LlamaIndex | Document indexing and retrieval |
| Vector Database | ChromaDB | Embedding storage and semantic search |
| Database | SQLite to PostgreSQL | Persistent application data |
| PDF Parsing | PyMuPDF | High-quality document text extraction |
| Frontend | Streamlit | Pure-Python interactive UI |
| Automation | Native Python | Reminders, scheduling, workflows |
| Deployment | Docker + Railway | Containerized cloud deployment |
| Version Control | Git + GitHub | Source management |

> **Note:** This project originally proposed LangChain, GPT-4, and n8n. After
> architectural review, the stack was modernized to **Claude + MCP + LlamaIndex** for
> tighter tool-use integration, and **native Python** replaced n8n so that all
> automation logic is version-controlled and fully testable.

---

## Project Phases

The platform is delivered in three phases representing the student's academic journey.

### Phase 1 — Campus Automation Hub
Streamlines day-to-day student logistics.
- Timetable extraction from PDFs or portals
- Deadline tracking and reminders
- Syllabus analysis (grading rules, learning outcomes)

### Phase 2 — AI Exam Preparation Assistant (Technical Centerpiece)
Intelligent, document-grounded exam readiness.
- RAG-powered Q&A over uploaded materials
- Adaptive quiz and mock-exam generation
- Confidence tracking and weakness detection
- Buffer-aware revision plan generation

### Phase 3 — AI Course Advisor and Campus Chatbot
Academic decision support and institutional knowledge.
- University GPT chatbot (RAG over handbooks and policies)
- Course recommendation engine
- Academic progress visualization

---

## MCP Tool Servers

Each phase is implemented as an independent MCP server exposing domain-specific tools
that Claude can call autonomously.

<details>
<summary><strong>Exam Prep Server (Phase 2)</strong></summary>

| Tool | Description |
|---|---|
| `upload_and_index` | Process a PDF into a searchable RAG index |
| `search_materials` | Semantic search over uploaded documents |
| `summarize_material` | Generate an exam-ready summary |
| `generate_quiz` | Create a quiz from indexed materials |
| `evaluate_answer` | Grade an answer and explain the result |
| `track_confidence` | Record a self-assessment score |
| `identify_weak_topics` | Determine which topics need review |
| `generate_revision_plan` | Build an adaptive study schedule |
| `create_mock_exam` | Generate a full timed practice exam |

</details>

<details>
<summary><strong>Advisor Server (Phase 3)</strong></summary>

| Tool | Description |
|---|---|
| `ask_university` | Answer institutional questions via RAG |
| `recommend_courses` | Suggest courses based on interests |
| `get_progress_dashboard` | Return GPA and credit progress data |
| `find_opportunities` | Surface scholarships and internships |

</details>

<details>
<summary><strong>Campus Server (Phase 1)</strong></summary>

| Tool | Description |
|---|---|
| `extract_timetable` | Parse a schedule PDF into structured data |
| `list_deadlines` | List upcoming deadlines |
| `create_reminder` | Schedule a reminder |
| `analyze_syllabus` | Extract grading rules and outcomes |

</details>

---

## Project Structure

```
agentic-ai-student-assistant/
|
+-- backend/
|   +-- main.py                 # FastAPI entry point
|   +-- config.py               # Settings (Pydantic)
|   +-- api/                    # API route handlers
|   +-- assistant/
|   |   +-- client.py           # Claude + MCP orchestration loop
|   |   +-- prompts.py          # System prompts
|   +-- mcp_servers/
|   |   +-- exam_prep_server.py # Phase 2 tools
|   |   +-- advisor_server.py   # Phase 3 tools
|   |   +-- campus_server.py    # Phase 1 tools
|   +-- rag/
|   |   +-- ingest.py           # PDF -> chunks -> embeddings
|   |   +-- retriever.py        # Semantic search
|   +-- database/
|   |   +-- models.py           # SQLAlchemy models
|   |   +-- connection.py       # DB session management
|   +-- core/
|       +-- auth.py             # JWT authentication
|       +-- security.py         # Password hashing
|
+-- frontend/
|   +-- app.py                  # Streamlit application
|
+-- data/                       # SQLite DB + ChromaDB (gitignored)
+-- uploads/                    # Uploaded documents (gitignored)
+-- tests/                      # Test suite
|
+-- .env.example                # Environment variable template
+-- requirements.txt            # Python dependencies
+-- docker-compose.yml          # Local orchestration
+-- Dockerfile                  # Container definition
+-- README.md
```

---

## Installation and Setup

### Prerequisites
- **Python 3.12+** — [download](https://www.python.org/downloads/)
- **Git** — [download](https://git-scm.com/downloads)
- An **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)
- *(Optional)* **Docker** — for containerized deployment

### 1. Clone the repository
```bash
git clone https://github.com/datazenith-labs/agentic-ai-student-assistant.git
cd agentic-ai-student-assistant
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# then open .env and add your Anthropic API key
```

---

## Configuration

Edit your `.env` file with the following values:

```env
# Anthropic / Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Embeddings (optional, for RAG; can use a local model instead)
OPENAI_API_KEY=your_openai_api_key_here

# Authentication
JWT_SECRET=generate_a_long_random_string_here
JWT_ALGORITHM=HS256

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/sage.db

# Storage paths
CHROMA_PERSIST_DIR=./data/chroma
UPLOAD_DIR=./uploads

# CORS (frontend origin)
CORS_ORIGINS=http://localhost:8501
```

> **Important:** Never commit your `.env` file. It is included in `.gitignore` by
> default.

---

## Running the Application

### Local Development

**Start the backend (FastAPI):**
```bash
uvicorn backend.main:app --reload --port 8000
```
The interactive API documentation will be available at `http://localhost:8000/docs`.

**Start the frontend (Streamlit), in a second terminal:**
```bash
streamlit run frontend/app.py
```
The application will open at `http://localhost:8501`.

### Docker (Optional)
```bash
docker-compose up --build
```

---

## Usage Examples

**Document-grounded question:**
> "Explain the difference between supervised and unsupervised learning, based on my
> uploaded lecture notes."

Claude invokes `search_materials` to retrieve relevant chunks from your documents,
then answers with citations to the specific pages.

**Quiz generation:**
> "Quiz me on chapter 3 with 5 medium-difficulty questions."

Claude invokes `generate_quiz`, retrieving content from your indexed material and
returning structured questions with answer keys.

**Revision planning:**
> "My exam is in 10 days. Build me a revision plan focusing on my weak topics."

Claude invokes `identify_weak_topics` followed by `generate_revision_plan` to produce
a personalized, buffer-aware schedule.

**University query:**
> "What is the policy on late assignment submissions?"

Claude invokes `ask_university`, performing RAG over the institutional handbook.

---

## Roadmap

- [x] Architecture and specification finalized
- [ ] **Phase 2** — Exam Preparation Assistant (RAG + MCP core)
- [ ] **Phase 3** — Course Advisor and University GPT chatbot
- [ ] **Phase 1** — Campus Automation Hub
- [ ] Cloud deployment (Railway + Streamlit)
- [ ] Migration from SQLite to PostgreSQL
- [ ] **Future:** Knowledge-graph synthesis across multiple sources
- [ ] **Future:** Lecture audio transcription (Whisper)
- [ ] **Future:** Next.js frontend for production polish

---

## Team

This project is developed by a 3-member student team as part of the **Elective
Project (CJ1)** module.

| Member | Focus Area |
|---|---|
| Abrar Fahim | AI / MCP Lead — tool servers, Claude integration, RAG |
| Tanjid Tonmoy | Backend — FastAPI, database, authentication, deployment |
| Minhazul Islam | Frontend and QA — Streamlit UI, testing, documentation |

---

## Contributing

This is an academic project and is not currently open for external contributions.
Team members should follow the workflow below:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes with clear messages: `git commit -m "Add quiz generation tool"`
3. Push and open a pull request for review.
4. Ensure all tests pass before merging to `main`.

---

## Contact

**Organization:** [datazenith-labs](https://github.com/datazenith-labs)
**Repository:** [agentic-ai-student-assistant](https://github.com/datazenith-labs/agentic-ai-student-assistant)

For questions about this project, please open an
[issue](https://github.com/datazenith-labs/agentic-ai-student-assistant/issues).

---

<p align="center">
  <em>Built with Claude, MCP, and RAG — demonstrating modern agentic AI engineering.</em>
</p>
