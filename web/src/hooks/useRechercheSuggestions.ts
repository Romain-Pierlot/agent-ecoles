"use client";

import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import { chercherPages, type PageSuggestion } from "@/lib/pagesRecherche";
import type { EtablissementRecherche, CommuneRecherche, RechercheResultats } from "@/lib/types";

// Logique de suggestions partagée entre RechercheChamp (champ desktop de
// la nav) et RechercheMobile (overlay plein écran) — un seul endroit pour
// le debounce, l'appel API et le repli sur les pages dédiées, pour ne pas
// dupliquer ce comportement entre les deux composants.

export const MIN_CARACTERES = 2;
const DEBOUNCE_MS = 150;
// Même valeur que RechercheBloc.tsx (limite par groupe, pas un total) —
// 4 établissements + 4 communes = 8 résultats max, cohérent avec la règle
// « 8 résultats, jamais de scroll » du tour 14.
const LIMITE_PAR_GROUPE = 4;

// Référence stable pour les cas « vide » — un `[]` littéral crée un
// nouveau tableau à chaque rendu, ce qui casse la comparaison de
// référence utilisée en aval (RechercheChamp réinitialise son curseur
// clavier quand `lignes` change de référence) et provoque une boucle de
// rendu infinie. Une seule constante réutilisée évite le problème.
const VIDE: never[] = [];

export type SuggestionsRecherche = {
  saisie: string;
  setSaisie: (v: string) => void;
  chargement: boolean;
  etablissements: EtablissementRecherche[];
  communes: CommuneRecherche[];
  /** Repli mots-clés → page dédiée, uniquement quand établissements ET
   * communes sont vides (décision actée : pas de mélange avec des
   * résultats réels, cf. docs/roadmap_technique.md). */
  pages: PageSuggestion[];
  /** Vrai uniquement une fois la requête résolue (pas pendant le debounce
   * ni le chargement) et sans aucune correspondance, toutes catégories
   * confondues. */
  aucunResultat: boolean;
};

export function useRechercheSuggestions(): SuggestionsRecherche {
  const [saisie, setSaisie] = useState("");
  const [resultats, setResultats] = useState<RechercheResultats | null>(null);
  const [chargement, setChargement] = useState(false);

  const requeteAssezLongue = saisie.trim().length >= MIN_CARACTERES;

  useEffect(() => {
    const q = saisie.trim();
    // Rien à déclencher pour une requête trop courte : pas besoin de
    // nettoyer `resultats` ici, le calcul ci-dessous ignore les résultats
    // (même périmés) tant que `requeteAssezLongue` est faux.
    if (q.length < MIN_CARACTERES) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      // Chargement affiché seulement une fois la requête réellement
      // lancée (après le debounce), pas dès la frappe — évite un
      // clignotement pendant que l'utilisateur tape encore.
      setChargement(true);
      fetch(`${API_URL}/recherche?q=${encodeURIComponent(q)}&limite=${LIMITE_PAR_GROUPE}`, {
        signal: controller.signal,
      })
        .then((reponse) => (reponse.ok ? (reponse.json() as Promise<RechercheResultats>) : null))
        .then((donnees) => {
          setResultats(donnees);
          setChargement(false);
        })
        .catch(() => {
          // Requête annulée (nouvelle frappe) ou API indisponible — même
          // raisonnement que RechercheBloc.tsx : l'autocomplétion est un
          // plus, pas un prérequis pour chercher.
          setChargement(false);
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [saisie]);

  const etablissements = useMemo(
    () => (requeteAssezLongue ? (resultats?.etablissements ?? VIDE) : VIDE),
    [requeteAssezLongue, resultats],
  );
  const communes = useMemo(
    () => (requeteAssezLongue ? (resultats?.communes ?? VIDE) : VIDE),
    [requeteAssezLongue, resultats],
  );
  const pages = useMemo(
    () =>
      requeteAssezLongue && etablissements.length === 0 && communes.length === 0
        ? chercherPages(saisie)
        : VIDE,
    [requeteAssezLongue, etablissements, communes, saisie],
  );
  const aucunResultat =
    requeteAssezLongue &&
    !chargement &&
    resultats !== null &&
    etablissements.length === 0 &&
    communes.length === 0 &&
    pages.length === 0;

  return { saisie, setSaisie, chargement, etablissements, communes, pages, aucunResultat };
}
