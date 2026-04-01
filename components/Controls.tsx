"use client";

interface ControlsProps {
  state: "idle" | "recording" | "processing" | "speaking";
  onToggleRecording: () => void;
}

export default function Controls({ state, onToggleRecording }: ControlsProps) {
  const isRecording = state === "recording";
  const isDisabled = state === "processing" || state === "speaking";

  return (
    <div className="flex flex-col items-center gap-3 py-4">
      <button
        onClick={onToggleRecording}
        disabled={isDisabled}
        className={`group relative flex h-16 w-16 items-center justify-center rounded-full transition-all duration-200
          ${
            isRecording
              ? "bg-red-500 hover:bg-red-600 scale-110"
              : isDisabled
              ? "bg-zinc-700 cursor-not-allowed opacity-50"
              : "bg-zinc-700 hover:bg-zinc-600 hover:scale-105 active:scale-95"
          }`}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
      >
        {isRecording ? (
          <div className="h-5 w-5 rounded-sm bg-white" />
        ) : (
          <svg className="h-7 w-7 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path
              d="M19 10v2a7 7 0 0 1-14 0v-2"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <line
              x1="12"
              y1="19"
              x2="12"
              y2="23"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        )}
      </button>
      <span className="text-xs text-zinc-500">
        {isRecording
          ? "Shtyp p\u00EBr t\u00EB ndaluar"
          : isDisabled
          ? ""
          : "Shtyp p\u00EBr t\u00EB regjistruar"}
      </span>
    </div>
  );
}
