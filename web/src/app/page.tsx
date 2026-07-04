"use client";

import { useState } from "react";
import { envoyerMessage } from "@/lib/api";

type Message = {
  role: "user" | "assistant" | "erreur";
  contenu: string;
};

function genererSessionId(): string {
  return crypto.randomUUID();
}

export default function PageChat() {
  const [sessionId] = useState(genererSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [enAttente, setEnAttente] = useState(false);

  async function envoyer(e: React.FormEvent) {
    e.preventDefault();
    const questionEnvoyee = question.trim();
    if (!questionEnvoyee || enAttente) return;

    setMessages((precedents) => [...precedents, { role: "user", contenu: questionEnvoyee }]);
    setQuestion("");
    setEnAttente(true);

    try {
      const reponse = await envoyerMessage(sessionId, questionEnvoyee);
      setMessages((precedents) => [...precedents, { role: "assistant", contenu: reponse }]);
    } catch {
      setMessages((precedents) => [
        ...precedents,
        { role: "erreur", contenu: "L'agent n'a pas répondu — l'API tourne-t-elle bien en local ?" },
      ]);
    } finally {
      setEnAttente(false);
    }
  }

  return (
    <main className="flex flex-col mx-auto w-full max-w-2xl h-screen p-4">
      <h1 className="text-lg font-semibold mb-4">agent-ecoles — test local</h1>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === "user"
                ? "text-right"
                : message.role === "erreur"
                ? "text-red-600 text-sm"
                : "text-left"
            }
          >
            <span
              className={
                message.role === "user"
                  ? "inline-block bg-blue-100 rounded-lg px-3 py-2"
                  : message.role === "erreur"
                  ? "inline-block"
                  : "inline-block bg-gray-100 rounded-lg px-3 py-2"
              }
            >
              {message.contenu}
            </span>
          </div>
        ))}
        {enAttente && <p className="text-sm text-gray-500">L&apos;agent réfléchit…</p>}
      </div>

      <form onSubmit={envoyer} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Posez une question sur un collège…"
          className="flex-1 border rounded-lg px-3 py-2"
          disabled={enAttente}
        />
        <button
          type="submit"
          disabled={enAttente}
          className="bg-blue-600 text-white rounded-lg px-4 py-2 disabled:opacity-50"
        >
          Envoyer
        </button>
      </form>
    </main>
  );
}
