"use client";

import { useRef, useState } from "react";
import { useLanguage, ui, pick } from "@/lib/i18n";
import { startRecording, type Recorder } from "@/lib/recordWav";

type Message = { role: "user" | "assistant"; content: string };

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/assistant/chat";

const TRANSCRIBE_URL = API_URL.replace(/\/chat$/, "/transcribe");

// One id per browser tab, sent with every request. The assistant service keys
// its conversation memory (last retrieved sources, last answer language, the
// previous question folded into retrieval) on this. Without it every visitor
// landed in the same "anonymous" bucket, so one person's "say that in English"
// could regenerate another person's answer, and one person's earlier question
// leaked into the next person's retrieval. sessionStorage (not localStorage)
// on purpose: a new tab is a new conversation, and nothing persists on shared
// devices after the tab closes.
function getSessionId(): string {
  const fallback = () =>
    `s-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  try {
    let id = sessionStorage.getItem("chungamama_session");
    if (!id) {
      id = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : fallback();
      sessionStorage.setItem("chungamama_session", id);
    }
    return id;
  } catch {
    return fallback(); // storage blocked: still unique for this page load
  }
}

export default function AssistantPage() {
  const { lang } = useLanguage();
  const t = ui.assistant;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef<string | null>(null);
  const recorder = useRef<Recorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [micNote, setMicNote] = useState<string | null>(null);

  // Voice input fills the text box instead of sending. Speech recognition
  // makes mistakes, and for a health question a mis-heard word should be
  // fixable by the person before it becomes the question.
  async function toggleMic() {
    if (transcribing) return;
    setMicNote(null);

    if (!recording) {
      try {
        recorder.current = await startRecording();
        setRecording(true);
      } catch (e) {
        console.error("Microphone unavailable:", e);
        setMicNote(pick(t.micDenied, lang));
      }
      return;
    }

    setRecording(false);
    setTranscribing(true);
    try {
      const wav = await recorder.current!.stop();
      const form = new FormData();
      form.append("audio", wav, "recording.wav");
      const res = await fetch(TRANSCRIBE_URL, { method: "POST", body: form });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const { text } = await res.json();
      if (!text) throw new Error("Empty transcript");
      setInput((prev) => (prev ? prev + " " : "") + text);
      setMicNote(pick(t.checkTranscript, lang));
    } catch (e) {
      console.error("Transcription failed:", e);
      setMicNote(pick(t.transcribeFailed, lang));
    } finally {
      recorder.current = null;
      setTranscribing(false);
    }
  }

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const next = [...messages, { role: "user" as const, content: input }];
    setMessages(next);
    setInput("");
    setLoading(true);

    if (!sessionId.current) sessionId.current = getSessionId();

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next, session_id: sessionId.current }),
      });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const result = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: result.reply }]);
    } catch (e: any) {
      // Technical detail goes to the console for you; the user sees a plain,
      // bilingual message that also tells them what to do if it's urgent.
      console.error("Assistant request failed:", e);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: pick(t.unavailable, lang) },
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
        {micNote && (
          <div className="px-4 py-2 text-xs text-ink-soft border-t border-line bg-[#FBFAF7]">
            {micNote}
          </div>
        )}
        <div className="flex gap-2 p-2.5 border-t border-line">
          <button
            onClick={toggleMic}
            disabled={loading || transcribing}
            aria-label={pick(recording ? t.micStop : t.micStart, lang)}
            className={`rounded-full px-4 text-sm font-semibold border disabled:opacity-40 ${
              recording ? "bg-red-600 text-white border-red-600" : "border-line text-blue-deep"
            }`}
          >
            {transcribing
              ? pick(t.transcribing, lang)
              : pick(recording ? t.micStop : t.micStart, lang)}
          </button>
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
