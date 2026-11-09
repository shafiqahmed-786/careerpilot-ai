"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { AiBadge, Badge, Card, ErrorNote, PageHeader, btnGhost, btnPrimary, inputClass } from "@/components/ui";
import {
  api,
  type ConversationDetail,
  type ConversationSummary,
  type MentorMessage,
  type MentorStatus,
} from "@/lib/api";
import { STARTERS, applyExchange, canSend, dropPending, pendingUserMessage, providerLabel, splitDemoNote } from "@/lib/mentor";

export default function MentorPage() {
  const [status, setStatus] = useState<MentorStatus | null>(null);
  const [list, setList] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MentorMessage[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const refreshList = useCallback(async () => setList(await api<ConversationSummary[]>("/api/v1/mentor/conversations")), []);

  useEffect(() => {
    Promise.all([api<MentorStatus>("/api/v1/mentor/status"), refreshList()])
      .then(([s]) => setStatus(s))
      .catch((e: Error) => setError(e.message));
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) setText(q);
  }, [refreshList]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, busy]);

  async function open(id: string) {
    setError("");
    try {
      const detail = await api<ConversationDetail>(`/api/v1/mentor/conversations/${id}`);
      setActiveId(id);
      setMessages(detail.messages);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not open the conversation");
    }
  }

  function newConversation() {
    setActiveId(null);
    setMessages([]);
    setError("");
  }

  async function remove(id: string) {
    try {
      await api(`/api/v1/mentor/conversations/${id}`, { method: "DELETE" });
      if (id === activeId) newConversation();
      await refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete the conversation");
    }
  }

  async function send(content: string) {
    if (!canSend(content, busy)) return;
    setBusy(true);
    setError("");
    const pending = pendingUserMessage(content.trim());
    setMessages((m) => [...m, pending]);
    setText("");
    try {
      let id = activeId;
      if (!id) {
        const created = await api<ConversationDetail>("/api/v1/mentor/conversations", { method: "POST", body: JSON.stringify({}) });
        id = created.id;
        setActiveId(id);
      }
      const exchange = await api<{ user_message: MentorMessage; assistant_message: MentorMessage }>(
        `/api/v1/mentor/conversations/${id}/messages`,
        { method: "POST", body: JSON.stringify({ content: content.trim() }) },
      );
      setMessages((m) => applyExchange(m, pending.id, exchange));
      await refreshList();
    } catch (e) {
      setMessages((m) => dropPending(m, pending.id));
      setText(content);
      setError(e instanceof Error ? e.message : "The mentor could not answer. Your message was not sent.");
    } finally {
      setBusy(false);
    }
  }

  const live = status?.mode === "groq";

  return (
    <>
      <PageHeader
        title="AI Career Mentor"
        subtitle="Answers use your profile, skill gaps, roadmap progress and resume evidence."
        actions={status ? <AiBadge live={live} label={live ? "AI Career Mentor" : "Guide Mode (Demo)"} /> : undefined}
      />
      {status && !live ? (
        <p className="mb-4 rounded-lg border border-warn/30 bg-warn/10 px-3 py-2 text-sm text-warn">
          Career Mentor is running in standard guide mode. Answers are assembled from your saved career profile and roadmap data.
        </p>
      ) : null}
      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <aside className="space-y-2">
          <button className={`${btnPrimary} w-full`} onClick={newConversation} type="button">New conversation</button>
          <ul className="space-y-1">
            {list.map((c) => (
              <li key={c.id} className={`group flex items-center justify-between rounded-lg px-3 py-2 text-sm ${c.id === activeId ? "bg-accent/10 text-accent" : "text-muted hover:bg-raised"}`}>
                <button className="min-w-0 flex-1 truncate text-left" onClick={() => open(c.id)} type="button">{c.title}</button>
                <button aria-label={`Delete ${c.title}`} className="ml-2 text-xs opacity-0 hover:text-bad focus:opacity-100 group-hover:opacity-100" onClick={() => remove(c.id)} type="button">✕</button>
              </li>
            ))}
            {list.length === 0 ? <li className="px-3 text-xs text-muted">No conversations yet.</li> : null}
          </ul>
        </aside>

        <Card className="flex min-h-[28rem] flex-col !p-0">
          <div className="flex-1 space-y-4 overflow-y-auto p-5" style={{ maxHeight: "60vh" }} aria-live="polite">
            {messages.length === 0 ? (
              <div>
                <p className="text-sm">Hi, I&apos;m your career mentor. I can see your target role, skill gaps and roadmap progress. Ask me what to do next, or try one of these:</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {STARTERS.map((s) => (
                    <button key={s} className={btnGhost} onClick={() => send(s)} type="button">{s}</button>
                  ))}
                </div>
                {status && !status.has_profile ? <p className="mt-4 text-xs text-warn">Complete your career profile so answers can be personal.</p> : null}
              </div>
            ) : null}
            {messages.map((m) => {
              const parts = m.role === "assistant" ? splitDemoNote(m.content) : { body: m.content, note: null };
              return (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${m.role === "user" ? "bg-accent text-[#0b0d14]" : "border border-line bg-raised"}`}>
                    <p className="whitespace-pre-wrap leading-relaxed">{parts.body}</p>
                    {m.role === "assistant" ? (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <Badge tone={m.provider === "groq" ? "accent" : "warn"}>{providerLabel(m.provider)}</Badge>
                        {m.notice ? <span className="text-xs text-warn">{m.notice}</span> : null}
                        {parts.note ? <span className="text-xs text-muted">{parts.note}</span> : null}
                      </div>
                    ) : null}
                  </div>
                </div>
              );
            })}
            {busy ? (
              <div className="flex justify-start" role="status" aria-label="The mentor is typing">
                <div className="flex gap-1 rounded-2xl border border-line bg-raised px-4 py-3">
                  {[0, 1, 2].map((i) => <span key={i} className="h-1.5 w-1.5 animate-dots rounded-full bg-muted" style={{ animationDelay: `${i * 0.15}s` }} />)}
                </div>
              </div>
            ) : null}
            <div ref={endRef} />
          </div>
          <div className="border-t border-line p-4">
            <ErrorNote message={error} />
            <form className="mt-2 flex items-end gap-2" onSubmit={(e) => { e.preventDefault(); void send(text); }}>
              <textarea
                aria-label="Message the mentor"
                className={`${inputClass} max-h-32 min-h-[2.5rem] flex-1 resize-none`}
                maxLength={2000}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(text); } }}
                placeholder="Ask about your skills, roadmap or next steps…"
                rows={1}
                value={text}
              />
              <button className={btnPrimary} disabled={!canSend(text, busy)} type="submit">Send</button>
            </form>
            <p className="mt-2 text-xs text-muted">Enter to send, Shift+Enter for a new line. The mentor cannot verify skills or guarantee outcomes.</p>
          </div>
        </Card>
      </div>
    </>
  );
}
