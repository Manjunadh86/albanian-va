import OpenAI from "openai";

const openai = new OpenAI();

export type Voice = "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer";

export async function synthesizeSpeech(
  text: string,
  voice: Voice = "nova"
): Promise<Buffer> {
  const response = await openai.audio.speech.create({
    model: "tts-1",
    voice,
    input: text,
    response_format: "mp3",
  });

  const arrayBuffer = await response.arrayBuffer();
  return Buffer.from(arrayBuffer);
}
