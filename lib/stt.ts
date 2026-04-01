import OpenAI from "openai";

const openai = new OpenAI();

export async function transcribeAudio(audioBuffer: Buffer, mimeType: string): Promise<string> {
  const ext = mimeType.includes("webm") ? "webm" : mimeType.includes("mp4") ? "mp4" : "wav";
  const uint8 = new Uint8Array(audioBuffer);
  const file = new File([uint8], `audio.${ext}`, { type: mimeType });

  const transcription = await openai.audio.transcriptions.create({
    model: "whisper-1",
    file,
    language: "sq", // Albanian language code
  });

  return transcription.text;
}
