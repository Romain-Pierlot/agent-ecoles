"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { hrefEtablissement, hrefCommune } from "@/lib/hrefsGeo";
import type { RechercheResultats } from "@/lib/types";
import { NOTATION_GRADIENTS } from "@/components/CarteCollege";
import { classeStatutSecteur } from "@/lib/tokens";

// Bloc de recherche ville/adresse — présent sur les pages hub (région,
// département), la page terminale ville et la page recherche (cf.
// docs/Design_system/hub_departement_comparateur/README.md). Extrait de
// ZoneHub pour éviter une 3ᵉ copie identique sur la page ville.
//
// Autocomplétion : appel direct à l'API (même pattern que lib/api.ts pour
// le chat — le navigateur appelle FastAPI directement, pas de proxy Next),
// avec un debounce et une borne de résultats réduite (`limite`) — même
// fonction de matching que la page de résultats, pas de logique dupliquée
// côté backend (cf. agent/tools/recherche_tool.py::rechercher).

const NB_SUGGESTIONS_PAR_GROUPE = 4;
const DEBOUNCE_MS = 300;

export function RechercheBloc({
  placeholder = "Rechercher un collège et/ou une ville, département…",
  valeurInitiale = "",
}: {
  placeholder?: string;
  // Pré-remplit le champ avec la requête déjà tapée (page /recherche avec
  // résultats) — pour affiner sans tout retaper, au lieu de repartir d'un
  // champ vide comme si on cherchait autre chose.
  valeurInitiale?: string;
}) {
  const [query, setQuery] = useState(valeurInitiale);
  const [focused, setFocused] = useState(false);
  const [resultats, setResultats] = useState<RechercheResultats | null>(null);
  const blurTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const q = query.trim();
    // Pas besoin de réinitialiser `resultats` ici : afficherDropdown exige
    // déjà querySoumise.length > 0, donc un `resultats` obsolète ne peut de
    // toute façon pas s'afficher une fois la requête vidée.
    if (!q) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetch(`${API_URL}/recherche?q=${encodeURIComponent(q)}&limite=${NB_SUGGESTIONS_PAR_GROUPE}`, {
        signal: controller.signal,
      })
        .then((reponse) => (reponse.ok ? (reponse.json() as Promise<RechercheResultats>) : null))
        .then((donnees) => {
          if (donnees) setResultats(donnees);
        })
        .catch(() => {
          // Requête annulée (nouvelle frappe) ou API indisponible — la
          // saisie native (soumission du formulaire) reste fonctionnelle
          // dans les deux cas, l'autocomplétion est un plus, pas un
          // prérequis pour chercher.
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  useEffect(() => {
    return () => {
      if (blurTimeout.current) clearTimeout(blurTimeout.current);
    };
  }, []);

  const querySoumise = query.trim();
  const afficherDropdown = focused && querySoumise.length > 0;
  const aucuneSuggestion =
    resultats !== null && resultats.etablissements.length === 0 && resultats.communes.length === 0;

  return (
    <div className="relative mt-6">
      <form
        action="/recherche"
        method="get"
        className="flex flex-wrap items-center gap-2.5 rounded-2xl border border-filet bg-white p-4"
      >
        <input
          type="text"
          name="q"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            // Délai avant de fermer le menu : laisse le temps au clic sur
            // une suggestion de se terminer avant que le dropdown disparaisse
            // (le blur de l'input se déclenche avant le click du lien).
            blurTimeout.current = setTimeout(() => setFocused(false), 150);
          }}
          placeholder={placeholder}
          autoComplete="off"
          className="min-w-[240px] flex-1 rounded-xl border border-filet-fonce bg-fond-carte px-3.5 py-2.5 text-[13.5px] text-texte outline-none placeholder:text-texte-doux/60"
        />
        <button
          type="submit"
          className="rounded-xl bg-action px-5 py-2.5 text-[13px] font-bold text-white hover:bg-action-dark"
        >
          Rechercher
        </button>

        {afficherDropdown && resultats && (
          <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-20 overflow-hidden rounded-2xl border-[1.5px] border-filet bg-white text-left shadow-[0_18px_44px_rgba(34,59,48,.16)]">
            {resultats.etablissements.length > 0 && (
              <div className="py-1">
                <div className="px-4 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wide text-texte-doux">
                  Établissements
                </div>
                {resultats.etablissements.slice(0, NB_SUGGESTIONS_PAR_GROUPE).map((e) => {
                  const gradient = e.notation ? NOTATION_GRADIENTS[e.notation] : null;
                  return (
                    <Link
                      key={e.uai}
                      href={hrefEtablissement(e)}
                      className="flex items-center gap-3 px-4 py-2 hover:bg-fond-carte/60"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-[13px] font-bold text-texte">{e.nom}</div>
                        <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
                          <span className="truncate text-[11px] text-texte-doux">
                            {e.commune} · {e.libelle_departement} ({e.code_departement})
                          </span>
                          <span className={`flex-none rounded-md px-1.5 py-px text-[9.5px] font-bold ${classeStatutSecteur(e.secteur)}`}>
                            {e.secteur}
                          </span>
                        </div>
                      </div>
                      <span
                        className="flex h-8 w-8 flex-none items-center justify-center rounded-lg font-baloo text-[11px] font-extrabold text-white"
                        style={
                          gradient
                            ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre }
                            : { backgroundColor: "var(--color-descriptif)" }
                        }
                      >
                        {e.notation ?? "—"}
                      </span>
                    </Link>
                  );
                })}
              </div>
            )}

            {resultats.communes.length > 0 && (
              <div className="border-t border-filet py-1">
                <div className="px-4 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wide text-texte-doux">
                  Communes
                </div>
                {resultats.communes.slice(0, NB_SUGGESTIONS_PAR_GROUPE).map((c) => (
                  <Link
                    key={`${c.commune}-${c.code_departement}`}
                    href={hrefCommune(c)}
                    className="flex items-center gap-3 px-4 py-2 hover:bg-fond-carte/60"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[13px] font-bold text-texte">{c.commune}</div>
                      <div className="truncate text-[11px] text-texte-doux">
                        {c.libelle_departement} ({c.code_departement}) · {c.nb_etablissements}{" "}
                        {c.nb_etablissements > 1 ? "collèges" : "collège"}
                      </div>
                    </div>
                    <span className="flex h-8 w-8 flex-none items-center justify-center rounded-lg bg-fond-sable text-[14px] text-texte-doux">
                      ⌂
                    </span>
                  </Link>
                ))}
              </div>
            )}

            {aucuneSuggestion && (
              <div className="px-4 py-3 text-[12.5px] text-texte-doux">
                Aucune correspondance directe pour « {querySoumise} ».
              </div>
            )}

            <button
              type="submit"
              className="w-full cursor-pointer border-t border-filet px-4 py-2.5 text-left text-[12.5px] font-bold text-action hover:bg-fond-carte/40"
            >
              Voir tous les résultats pour « {querySoumise} » →
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
