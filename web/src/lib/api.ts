// Appel à l'API Python (api/main.py) — séparé de l'affichage (page.tsx),
// pour rester testable et remplaçable seul (ex. si l'URL change en prod).

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function envoyerMessage(
  sessionId: string,
  question: string
): Promise<string> {
  const reponse = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });

  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }

  const donnees = (await reponse.json()) as { reponse: string };
  return donnees.reponse;
}
