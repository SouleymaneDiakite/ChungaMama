"use client";

import { useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";

type Message = { role: "user" | "assistant"; content: string };

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/assistant/chat";

export default function AssistantPage() {
  const { lang } = useLanguage();
  const t = ui.assistant;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!input.trim()) return;
    const next = [...messages, { role: "user" as const, content: input }];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next }),
      });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const result = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: result.reply }]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `${pick(t.errorPrefix, lang)} ${e.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="py-12 max-w-xl mx-auto">
      <h1 className="font-display text-2xl text-blue-deep mb-5">{pick(t.title, lang)}</h1>
      <div className="border border-line rounded-2xl overflow-hidden bg-white">
        <div className="h-[420px] overflow-y-auto p-4 flex flex-col gap-2.5 bg-[#FBFAF7]">
          {/* Greeting is rendered live in the current language, not stored in
              message state, so switching languages mid-session updates it
              immediately rather than freezing whatever language loaded first. */}
          <div className="max-w-[80%] self-start bg-[#EFEAE0] text-ink rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm leading-relaxed">
            {pick(t.greeting, lang)}
          </div>

          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
                m.role === "user"
                  ? "self-end bg-blue-mid text-white rounded-br-sm"
                  : "self-start bg-[#EFEAE0] text-ink rounded-bl-sm"
              }`}
            >
              {m.content}
            </div>
          ))}
          {loading && (
            <div className="self-start text-xs text-ink-soft italic">{pick(t.thinking, lang)}</div>
          )}
        </div>
        <div className="flex gap-2 p-2.5 border-t border-line">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder={pick(t.placeholder, lang)}
            className="flex-1 border border-line rounded-full px-4 py-2 text-sm outline-none focus:border-blue-mid"
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="bg-blue-deep text-white rounded-full px-5 text-sm font-semibold disabled:opacity-40"
          >
            {pick(t.send, lang)}
          </button>
        </div>
      </div>
      <p className="text-xs text-ink-soft mt-3">{pick(t.disclaimer, lang)}</p>
    </main>
  );
}
