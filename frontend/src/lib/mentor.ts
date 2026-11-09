import type { MentorMessage } from "@/lib/api";

export const STARTERS = [
  "What should I learn first to become an AI Engineer?",
  "Analyze my biggest skill gaps.",
  "Which projects should I build next?",
  "Am I ready to apply for internships?",
  "Help me improve my current learning strategy.",
  "Explain why this skill is important for my target role.",
  "What should I focus on this week?",
];

export function providerLabel(provider: string | null | undefined): string {
  if (provider === "groq") return "AI Mentor";
  return "Guided Answer";
}

export function pendingUserMessage(text: string): MentorMessage {
  return {
    id: `pending-${Date.now()}`,
    role: "user",
    content: text,
    provider: null,
    notice: null,
    created_at: new Date().toISOString(),
  };
}

/** Replace the optimistic message with the saved exchange from the API. */
export function applyExchange(
  messages: MentorMessage[],
  pendingId: string,
  exchange: { user_message: MentorMessage; assistant_message: MentorMessage },
): MentorMessage[] {
  return [...messages.filter((message) => message.id !== pendingId), exchange.user_message, exchange.assistant_message];
}

export function dropPending(messages: MentorMessage[], pendingId: string): MentorMessage[] {
  return messages.filter((message) => message.id !== pendingId);
}

/** Demo replies end with an italic note. Split it out so the UI can show it as a muted caption. */
export function splitDemoNote(content: string): { body: string; note: string | null } {
  const match = content.match(/^([\s\S]*?)\n\n_([^_][\s\S]*)_\s*$/);
  if (!match) return { body: content, note: null };
  return { body: match[1], note: match[2] };
}

export function canSend(text: string, busy: boolean): boolean {
  return !busy && text.trim().length > 0 && text.length <= 2000;
}
