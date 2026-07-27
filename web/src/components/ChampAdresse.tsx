"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { recupererSuggestionsAdresse } from "@/lib/secteur";
import type { SuggestionAdresse } from "@/lib/types";

const DEBOUNCE_MS = 300;

// Champ adresse avec autocomplétion — même pattern que RechercheBloc.tsx
// (debounce, dropdown, délai de blur pour laisser le clic aboutir), mais un
// composant distinct : source différente (API BAN via /secteur/adresses,
// pas notre propre recherche par nom) et sélection d'une suggestion =
// navigation directe (pas de recherche libre de secours).
//
// Corrige un vrai problème signalé (2026-07-23) : soumettre du texte libre
// laissait le backend résoudre l'adresse sur le seul premier résultat BAN
// (geocoder(), limit=1) — une saisie incomplète ("30 rue jean") matche 5
// villes différentes en France, et affichait un collège de secteur basé
// sur une adresse jamais réellement choisie par l'utilisateur. Choisir une
// suggestion explicite élimine cette ambiguïté ; la soumission en texte
// libre (Entrée sans sélection) reste un repli, pas le chemin principal.
export function ChampAdresse({ adresseInitiale = "" }: { adresseInitiale?: string }) {
  const router = useRouter();
  const [adresse, setAdresse] = useState(adresseInitiale);
  const [focus, setFocus] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestionAdresse[]>([]);
  const blurTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const q = adresse.trim();
    // Pas besoin de réinitialiser `suggestions` ici (même raisonnement que
    // RechercheBloc.tsx) : afficherDropdown exige déjà q.length > 0, donc
    // une liste obsolète ne peut de toute façon pas s'afficher une fois le
    // champ vidé.
    if (!q) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      recupererSuggestionsAdresse(q, { signal: controller.signal })
        .then((donnees) => setSuggestions(donnees))
        .catch(() => {
          // Requête annulée (nouvelle frappe) ou API indisponible — la
          // soumission en texte libre reste possible dans les deux cas.
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [adresse]);

  useEffect(() => {
    return () => {
      if (blurTimeout.current) clearTimeout(blurTimeout.current);
    };
  }, []);

  const naviguerVers = (valeur: string) => {
    const v = valeur.trim();
    if (!v) return;
    setAdresse(v);
    router.push(`/carte-scolaire?adresse=${encodeURIComponent(v)}`);
  };

  const afficherDropdown = focus && adresse.trim().length > 0 && suggestions.length > 0;

  return (
    <div className="max-w-[600px]">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          naviguerVers(adresse);
        }}
      >
        <div className="relative">
          <div className="flex h-[58px] items-center gap-3 rounded-[18px] bg-white pl-5 pr-2 shadow-[0_8px_24px_rgba(40,28,14,.10)] focus-within:ring-2 focus-within:ring-action/30 md:h-[74px] md:gap-3.5 md:rounded-[22px] md:pl-6 md:pr-2.5">
            <span className="flex-none text-[19px] leading-none">📍</span>
            <input
              id="champ-adresse-input"
              type="text"
              value={adresse}
              onChange={(e) => setAdresse(e.target.value)}
              onFocus={() => setFocus(true)}
              onBlur={() => {
                // Délai avant de fermer le menu : laisse le temps au clic sur
                // une suggestion de se terminer (même pattern que RechercheBloc).
                blurTimeout.current = setTimeout(() => setFocus(false), 150);
              }}
              placeholder="18 avenue des Fleurs, 06000 Nice"
              aria-label="Votre adresse"
              autoComplete="off"
              className="min-w-0 flex-1 border-none bg-transparent text-[15px] text-texte outline-none placeholder:text-[#9A9086] md:text-[17px]"
            />
            <button
              type="submit"
              className="hidden h-14 flex-none items-center whitespace-nowrap rounded-[16px] bg-action px-7 text-[16px] font-bold text-white hover:bg-action-dark md:flex"
            >
              Trouver mon secteur
            </button>
          </div>

          {afficherDropdown && (
            <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-20 overflow-hidden rounded-2xl border-[1.5px] border-filet bg-white text-left shadow-[0_18px_44px_rgba(34,59,48,.16)]">
              {suggestions.map((s) => (
                <button
                  key={s.label}
                  type="button"
                  onMouseDown={() => naviguerVers(s.label)}
                  className="flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-fond-carte/60"
                >
                  <span className="flex-none text-[13px] text-texte-doux">📍</span>
                  <span className="truncate text-[13px] font-semibold text-texte">{s.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          className="mt-2.5 flex h-[52px] w-full items-center justify-center rounded-[16px] bg-action text-[16px] font-bold text-white hover:bg-action-dark md:hidden"
        >
          Trouver mon secteur
        </button>
      </form>
    </div>
  );
}
