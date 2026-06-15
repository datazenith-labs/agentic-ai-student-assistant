// src/components/home/widgets/QuickUpload.tsx
//
// Right-column widget: drag-and-drop file upload zone for adding documents
// to the RAG knowledge base. Accepts PDF, DOCX, PPTX up to 20MB.
//
// For now: drop / click both just console.log the files. Phase 12.6 wires
// this to POST /api/uploads which kicks off chunking + embedding + ChromaDB
// ingest.
//
// Why client component: drag-and-drop handlers + file input ref.
//
// "View all" goes to /uploads which is the full upload center page.

"use client";

import { useRef, useState } from "react";
import { CloudUpload } from "lucide-react";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const ALLOWED = [".pdf", ".docx", ".pptx"];
const MAX_MB = 20;

export function QuickUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    // TODO (Phase 12.6): validate size + extension, POST to /api/uploads,
    // show progress and ingest status.
    console.log(
      "[QuickUpload]",
      Array.from(files).map((f) => ({ name: f.name, size: f.size }))
    );
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-semibold text-sm">Quick Upload</h3>
        <Link
          href="/uploads"
          className="text-xs font-medium text-violet-600 dark:text-violet-400 hover:underline"
        >
          View all
        </Link>
      </div>
      <p className="text-xs text-muted-foreground mb-4">
        Upload your notes & materials
      </p>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        aria-label="Upload files: click to browse, or drag and drop"
        className={cn(
          "w-full rounded-lg border-2 border-dashed flex flex-col items-center justify-center gap-2 py-6 px-4 cursor-pointer transition-all",
          isDragOver
            ? "border-violet-500 bg-violet-50 dark:bg-violet-950/30"
            : "border-border bg-muted/20 hover:border-violet-300 dark:hover:border-violet-800 hover:bg-violet-50/50 dark:hover:bg-violet-950/20"
        )}
      >
        <div className="size-10 rounded-full bg-violet-100 dark:bg-violet-950/40 flex items-center justify-center text-violet-600 dark:text-violet-400">
          <CloudUpload className="size-5" />
        </div>
        <div className="text-center leading-tight">
          <div className="text-sm font-medium">Drag & drop files here</div>
          <div className="text-[10px] text-muted-foreground mt-0.5">
            PDF, DOCX, PPTX up to {MAX_MB}MB
          </div>
        </div>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED.join(",")}
        multiple
        onChange={(e) => handleFiles(e.target.files)}
        className="hidden"
        aria-hidden
      />
    </Card>
  );
}