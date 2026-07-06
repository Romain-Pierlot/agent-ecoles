// Appel à l'API Python (api/main.py) — séparé de l'affichage (page.tsx),
// pour rester testable et remplaçable seul (ex. si l'URL change en prod).

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type OptionChoix = {
  label: string;
  valeur: Record<string, string>;
};

export type GroupeChoix = {
  titre: string;
  options: OptionChoix[];
};

export type Choix = {
  type: string; // "zone", "noms" ou "voir_plus"
  groupes: GroupeChoix[];
};

export type ReponseChat = {
  reponse: string;
  choix: Choix | null;
};

async function appelerChat(
  sessionId: string,
  corps: Record<string, unknown>
): Promise<ReponseChat> {
  const reponse = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, ...corps }),
  });

  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }

  return (await reponse.json()) as ReponseChat;
}

export function envoyerMessage(sessionId: string, question: string): Promise<ReponseChat> {
  return appelerChat(sessionId, { question });
}

// Résout un choix cliqué sur une clarification ambiguë (zone ou noms
// d'établissements, cf. graph_router.poser_resolution_choix côté backend) —
// ne renvoie jamais de texte libre, uniquement la valeur structurée du
// bouton cliqué.
export function envoyerResolution(
  sessionId: string,
  resolution: Record<string, unknown>
): Promise<ReponseChat> {
  return appelerChat(sessionId, { resolution });
}

// Construit le corps de résolution attendu par l'API à partir du type de
// clarification (porté par Choix.type) et de la valeur du bouton cliqué —
// les trois types n'ont pas la même forme côté backend.
export function construireResolution(
  type: string,
  valeur: Record<string, string>
): Record<string, unknown> {
  if (type === "zone") {
    return { type: "zone", commune: valeur.commune, code_departement: valeur.code_departement };
  }
  if (type === "voir_plus") {
    return { type: "voir_plus", secteur: valeur.secteur };
  }
  return { type: "noms", choix: { [valeur.nom]: valeur.uai } };
}
