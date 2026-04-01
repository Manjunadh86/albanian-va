import { NextRequest, NextResponse } from "next/server";
import { transcribeAudio } from "@/lib/stt";
import { generateResponse, Message } from "@/lib/llm";
import { synthesizeSpeech, Voice } from "@/lib/tts";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const audioFile = formData.get("audio") as File | null;
    const historyRaw = formData.get("history") as string | null;
    const voice = (formData.get("voice") as Voice) || "nova";

    if (!audioFile) {
      return NextResponse.json({ error: "No audio file provided" }, { status: 400 });
    }

    const audioBuffer = Buffer.from(await audioFile.arrayBuffer());
    const conversationHistory: Message[] = historyRaw ? JSON.parse(historyRaw) : [];

    // Step 1: Speech-to-Text
    const transcript = await transcribeAudio(audioBuffer, audioFile.type);

    if (!transcript.trim()) {
      return NextResponse.json(
        { error: "Could not understand audio", transcript: "" },
        { status: 400 }
      );
    }

    // Step 2: LLM Response
    const responseText = await generateResponse(transcript, conversationHistory);

    // Step 3: Text-to-Speech
    const audioResponse = await synthesizeSpeech(responseText, voice);

    // Return JSON with transcript + response text, and audio as base64
    return NextResponse.json({
      transcript,
      response: responseText,
      audio: audioResponse.toString("base64"),
    });
  } catch (error) {
    console.error("Voice pipeline error:", error);
    const message = error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
