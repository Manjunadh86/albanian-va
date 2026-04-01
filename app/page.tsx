"use client";

import { useState, useCallback, useRef } from "react";
import VoiceOrb from "@/components/VoiceOrb";
import TranscriptPanel, { TranscriptEntry } from "@/components/TranscriptPanel";
import Controls from "@/components/Controls";
import { AudioRecorder, playBase64Audio } from "@/lib/audio";

type AppState = "idle" | "recording" | "processing" | "speaking";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [state, setState] = useState<AppState>("idle");
  const [entries, setEntries] = useState<TranscriptEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);
  const historyRef = useRef<Message[]>([]);

  const handleToggleRecording = useCallback(async () => {
    setError(null);

    if (state === "recording") {
      // Stop recording and process
      if (!recorderRef.current) return;
      setState("processing");

      try {
        const audioBlob = await recorderRef.current.stop();
        recorderRef.current = null;

        // Send to API
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        formData.append("history", JSON.stringify(historyRef.current));
        formData.append("voice", "nova");

        const res = await fetch("/api/voice", { method: "POST", body: formData });
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || "Pipeline failed");
        }

        // Add user transcript
        const userId = crypto.randomUUID();
        const assistantId = crypto.randomUUID();

        setEntries((prev) => [
          ...prev,
          { id: userId, role: "user", text: data.transcript },
          { id: assistantId, role: "assistant", text: data.response },
        ]);

        // Update conversation history
        historyRef.current = [
          ...historyRef.current,
          { role: "user", content: data.transcript },
          { role: "assistant", content: data.response },
        ];

        // Play audio response
        setState("speaking");
        await playBase64Audio(data.audio);
        setState("idle");
      } catch (err) {
        const message = err instanceof Error ? err.message : "Something went wrong";
        setError(message);
        setState("idle");
      }
    } else if (state === "idle") {
      // Start recording
      try {
        const recorder = new AudioRecorder();
        await recorder.start();
        recorderRef.current = recorder;
        setState("recording");
      } catch {
        setError("Nuk mund të aksesoj mikrofonin. Lejo aksesin në mikrofon.");
      }
    }
  }, [state]);

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-white">
      {/* Header */}
      <header className="flex items-center justify-center py-4 border-b border-zinc-800/50">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center">
            <span className="text-sm font-bold">AL</span>
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight">Asistenti Shqiptar</h1>
            <p className="text-[11px] text-zinc-500">Albanian Voice Assistant</p>
          </div>
        </div>
      </header>

      {/* Transcript area */}
      <TranscriptPanel entries={entries} />

      {/* Voice Orb + Controls */}
      <div className="flex flex-col items-center gap-2 py-6 border-t border-zinc-800/50 bg-zinc-950/80 backdrop-blur">
        <VoiceOrb state={state} />
        <Controls state={state} onToggleRecording={handleToggleRecording} />

        {/* Error message */}
        {error && (
          <div className="mx-4 px-4 py-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-300 text-xs text-center max-w-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
