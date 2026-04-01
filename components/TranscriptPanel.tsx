"use client";

import { useEffect, useRef } from "react";

export interface TranscriptEntry {
  id: string;
  role: "user" | "assistant";
  text: string;
}

interface TranscriptPanelProps {
  entries: TranscriptEntry[];
}

export default function TranscriptPanel({ entries }: TranscriptPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-4">
        <p className="text-zinc-500 text-sm text-center">
          Shtyp butonin e mikrofonit dhe fillo t&euml; flasësh shqip
          <br />
          <span className="text-zinc-600 text-xs">
            Press the mic button and start speaking Albanian
          </span>
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin">
      {entries.map((entry) => (
        <div
          key={entry.id}
          className={`flex ${entry.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              entry.role === "user"
                ? "bg-blue-600 text-white rounded-br-md"
                : "bg-zinc-800 text-zinc-100 rounded-bl-md"
            }`}
          >
            <span className="block text-[10px] uppercase tracking-wider mb-1 opacity-60">
              {entry.role === "user" ? "Ti" : "Asistenti"}
            </span>
            {entry.text}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
