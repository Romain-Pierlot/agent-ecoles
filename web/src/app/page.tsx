"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  envoyerMessage,
  envoyerResolution,
  construireResolution,
  type Choix,
} from "@/lib/api";

type Message = {
  role: "user" | "assistant" | "erreur";
  contenu: string;
  choix?: Choix | null;
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
      const { reponse, choix } = await envoyerMessage(sessionId, questionEnvoyee);
      setMessages((precedents) => [...precedents, { role: "assistant", contenu: reponse, choix }]);
    } catch {
      setMessages((precedents) => [
        ...precedents,
        { role: "erreur", contenu: "L'agent n'a pas répondu — l'API tourne-t-elle bien en local ?" },
      ]);
    } finally {
      setEnAttente(false);
    }
  }

  async function cliquerChoix(type: string, label: string, valeur: Record<string, string>) {
    if (enAttente) return;

    setMessages((precedents) => [...precedents, { role: "user", contenu: label }]);
    setEnAttente(true);

    try {
      const resolution = construireResolution(type, valeur);
      const { reponse, choix } = await envoyerResolution(sessionId, resolution);
      setMessages((precedents) => [...precedents, { role: "assistant", contenu: reponse, choix }]);
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
    <main className="flex flex-col mx-auto w-full max-w-2xl h-screen p-4 bg-white text-gray-900">
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
            {message.role === "assistant" ? (
              <div className="inline-block max-w-full">
                <div className="prose prose-sm max-w-none bg-gray-100 rounded-lg px-3 py-2 text-left">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.contenu}</ReactMarkdown>
                </div>
                {message.choix && (
                  <div className="mt-2 space-y-2">
                    {message.choix.groupes.map((groupe) => (
                      <div key={groupe.titre} className="flex flex-wrap gap-2">
                        {groupe.options.map((option) => (
                          <button
                            key={option.label}
                            type="button"
                            disabled={enAttente}
                            onClick={() =>
                              cliquerChoix(message.choix!.type, option.label, option.valeur)
                            }
                            className="border border-blue-300 text-blue-700 rounded-full px-3 py-1 text-sm hover:bg-blue-50 disabled:opacity-50"
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <span
                className={
                  message.role === "user"
                    ? "inline-block bg-blue-100 rounded-lg px-3 py-2"
                    : "inline-block"
                }
              >
                {message.contenu}
              </span>
            )}
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
