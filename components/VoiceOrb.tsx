"use client";

interface VoiceOrbProps {
  state: "idle" | "recording" | "processing" | "speaking";
}

export default function VoiceOrb({ state }: VoiceOrbProps) {
  const stateStyles = {
    idle: "bg-gradient-to-br from-zinc-700 to-zinc-900 shadow-lg shadow-zinc-800/50",
    recording:
      "bg-gradient-to-br from-red-500 to-red-700 shadow-lg shadow-red-500/50 animate-pulse",
    processing:
      "bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/50 animate-spin-slow",
    speaking:
      "bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-lg shadow-emerald-500/50 animate-pulse",
  };

  const ringStyles = {
    idle: "border-zinc-600/30",
    recording: "border-red-400/40 animate-ping-slow",
    processing: "border-amber-400/30 animate-spin-reverse",
    speaking: "border-emerald-400/40 animate-ping-slow",
  };

  const labels = {
    idle: "Gati",
    recording: "Po d\u00ebgjoj...",
    processing: "Po mendoj...",
    speaking: "Po flas...",
  };

  return (
    <div className="relative flex flex-col items-center gap-6">
      {/* Outer ring */}
      <div className="relative flex items-center justify-center">
        <div
          className={`absolute h-48 w-48 rounded-full border-2 ${ringStyles[state]} transition-all duration-500`}
        />
        <div
          className={`absolute h-56 w-56 rounded-full border ${ringStyles[state]} opacity-50 transition-all duration-700`}
        />
        {/* Main orb */}
        <div
          className={`h-36 w-36 rounded-full ${stateStyles[state]} transition-all duration-300 flex items-center justify-center`}
        >
          <OrbIcon state={state} />
        </div>
      </div>
      {/* Status label */}
      <span className="text-sm font-medium text-zinc-400 tracking-wide uppercase">
        {labels[state]}
      </span>
    </div>
  );
}

function OrbIcon({ state }: { state: string }) {
  if (state === "recording") {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="w-1 bg-white/90 rounded-full animate-wave"
            style={{
              height: `${12 + Math.random() * 20}px`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    );
  }

  if (state === "processing") {
    return (
      <svg className="h-10 w-10 text-white/80 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3" />
        <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (state === "speaking") {
    return (
      <svg className="h-10 w-10 text-white/90" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  // idle
  return (
    <svg className="h-10 w-10 text-zinc-400" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
