import OpenAI from "openai";

const openai = new OpenAI();

export interface Message {
  role: "user" | "assistant";
  content: string;
}

const SYSTEM_PROMPT = `Ti je një asistent virtual inteligjent që flet shqip.
Përgjigju gjithmonë në shqip, pavarësisht gjuhës së pyetjes.
Ji i sjellshëm, i qartë dhe i dobishëm. Përgjigjet e tua duhet të jenë koncize por informuese.
Nëse dikush flet në një gjuhë tjetër, përgjigju në shqip duke i treguar se ti flet vetëm shqip.

You are an intelligent virtual assistant that speaks Albanian.
Always respond in Albanian, regardless of the language of the question.
Be polite, clear, and helpful. Your responses should be concise but informative.`;

export async function generateResponse(
  userMessage: string,
  conversationHistory: Message[]
): Promise<string> {
  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: "system", content: SYSTEM_PROMPT },
    ...conversationHistory.map((msg) => ({
      role: msg.role as "user" | "assistant",
      content: msg.content,
    })),
    { role: "user", content: userMessage },
  ];

  const completion = await openai.chat.completions.create({
    model: "gpt-4o",
    messages,
    max_tokens: 500,
    temperature: 0.7,
  });

  return completion.choices[0]?.message?.content || "Më falni, nuk munda të përgjigjem.";
}
