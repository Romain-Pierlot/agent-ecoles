"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { NOM_ASSISTANT } from "@/lib/constants";
import { metaEtablissement, metaCommune, surlignerInverse } from "@/lib/rechercheAffichage";
import { construireLignes, hrefLigne, type LigneMenu } from "@/lib/rechercheMenu";
import { useRechercheSuggestions, MIN_CARACTERES } from "@/hooks/useRechercheSuggestions";
import { GaletAgent } from "@/components/GaletAgent";

// Champ de recherche PERMANENT de la barre de nav (tour 14a de la
// maquette refonte terracotta). Remplace le lien nav « Rechercher » :
// valider une requête (Entrée sur la ligne « voir tous les résultats »,
// ou directement sur une suggestion) mène à la même destination que
// l'ancien lien menait déjà (page /recherche ou fiche établissement/
// commune) — c'est le champ qui fait le travail, plus le lien.
//
// Construction des lignes du menu et résolution de leur destination :
// voir lib/rechercheMenu.ts, partagé avec RechercheMobile pour garantir
// exactement le même ordre/comportement des deux côtés.
//
// Décisions figées côté design, ne pas « optimiser » sans en reparler
// (cf. docs/roadmap_technique.md et la conversation de conception) :
//  - toujours visible, hauteur 36 px identique au repos et au focus ;
//  - champ 300 px, menu 480 px FIXE ancré à gauche, une ligne par résultat ;
//  - aucun résultat nulle part : requête rappelée + reformulation +
//    2 liens fixes (jamais une impasse sèche).

export function RechercheChamp({
  hrefAssistant = "/assistant",
  placeholder = "Collège, ville, code postal…",
}: {
  hrefAssistant?: string;
  placeholder?: string;
}) {
  const router = useRouter();
  const idListe = useId();
  const champRef = useRef<HTMLInputElement>(null);
  const conteneurRef = useRef<HTMLDivElement>(null);

  const { saisie, setSaisie, chargement, etablissements, communes, pages, aucunResultat } =
    useRechercheSuggestions();
  const [ouvert, setOuvert] = useState(false);
  const [actif, setActif] = useState(0);

  const lignes = useMemo(
    () => construireLignes({ etablissements, communes, pages, aucunResultat }),
    [etablissements, communes, pages, aucunResultat],
  );

  // Réinitialise le curseur clavier quand les lignes changent (nouveaux
  // résultats) — ajusté pendant le rendu plutôt que dans un effet séparé,
  // pour éviter un rendu supplémentaire (cf. règle react-hooks/set-state-in-effect).
  const [lignesPrecedentes, setLignesPrecedentes] = useState(lignes);
  if (lignes !== lignesPrecedentes) {
    setLignesPrecedentes(lignes);
    setActif(0);
  }

  // Raccourci « / » pour saisir (ignoré si on est déjà dans un champ).
  useEffect(() => {
    function surTouche(e: KeyboardEvent) {
      const cible = e.target as HTMLElement | null;
      const dansUnChamp =
        cible && (cible.tagName === "INPUT" || cible.tagName === "TEXTAREA" || cible.isContentEditable);
      if (e.key === "/" && !dansUnChamp) {
        e.preventDefault();
        champRef.current?.focus();
      }
    }
    document.addEventListener("keydown", surTouche);
    return () => document.removeEventListener("keydown", surTouche);
  }, []);

  // Clic hors du composant → fermeture.
  useEffect(() => {
    function surClic(e: MouseEvent) {
      if (!conteneurRef.current?.contains(e.target as Node)) setOuvert(false);
    }
    document.addEventListener("mousedown", surClic);
    return () => document.removeEventListener("mousedown", surClic);
  }, []);

  const menuVisible = ouvert && saisie.trim().length >= MIN_CARACTERES;

  function aller(ligne: LigneMenu | undefined) {
    if (!ligne) return;
    setOuvert(false);
    champRef.current?.blur();
    router.push(hrefLigne(ligne, saisie.trim(), hrefAssistant));
  }

  function surTouche(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      setOuvert(false);
      return;
    }
    if (!menuVisible || lignes.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActif((i) => (i + 1) % lignes.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActif((i) => (i - 1 + lignes.length) % lignes.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      aller(lignes[actif]);
    }
  }

  return (
    <div ref={conteneurRef} className="relative w-full max-w-[300px] flex-1">
      <div className="flex h-9 items-center gap-2 rounded-[9px] border border-filet bg-white pl-3 pr-2.5 focus-within:border-action focus-within:ring-[3px] focus-within:ring-action/15">
        <span aria-hidden className="flex-none text-[14px] text-filet-fonce">⌕</span>
        <input
          ref={champRef}
          value={saisie}
          onChange={(e) => {
            setSaisie(e.target.value);
            setOuvert(true);
          }}
          onFocus={() => setOuvert(true)}
          onKeyDown={surTouche}
          placeholder={placeholder}
          aria-label="Rechercher un collège ou une commune"
          role="combobox"
          aria-expanded={menuVisible}
          aria-controls={idListe}
          aria-autocomplete="list"
          aria-activedescendant={menuVisible && lignes.length > 0 ? `${idListe}-${actif}` : undefined}
          className="min-w-0 flex-1 bg-transparent font-ui text-[12.5px] font-medium text-texte outline-none placeholder:font-medium placeholder:text-filet-fonce"
        />
        {saisie ? (
          <button
            type="button"
            onClick={() => {
              setSaisie("");
              champRef.current?.focus();
            }}
            aria-label="Effacer la recherche"
            className="flex-none px-0.5 font-ui text-[13px] font-semibold text-filet-fonce hover:text-texte"
          >
            ×
          </button>
        ) : (
          <kbd
            aria-hidden
            className="flex-none rounded border border-filet bg-fond-creme px-1.5 py-px font-ui text-[9.5px] font-bold text-filet-fonce"
          >
            /
          </kbd>
        )}
      </div>

      {menuVisible && (
        <div
          id={idListe}
          role="listbox"
          className="absolute left-0 top-[calc(100%+8px)] z-50 w-[480px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-[10px] border border-filet bg-white shadow-[0_18px_40px_rgba(40,28,14,.22)]"
        >
          {lignes.length === 0 && (
            <div className="px-3.5 py-3 font-ui text-[12.5px] text-texte-doux">
              {chargement ? "Recherche en cours…" : "Continuez à taper pour chercher."}
            </div>
          )}

          {aucunResultat && (
            <div className="px-3.5 pb-1.5 pt-3 font-ui text-[12.5px] leading-[1.5] text-texte-doux">
              Aucun résultat pour « {saisie.trim()} ». Vérifiez l&apos;orthographe, ou essayez avec juste
              le nom de la ville.
            </div>
          )}

          {lignes.map((ligne, index) => {
            const precedent = lignes[index - 1];
            const debutSection = precedent === undefined || precedent.type !== ligne.type;
            const surbrille = index === actif;
            const id = `${idListe}-${index}`;

            if (ligne.type === "etablissement" || ligne.type === "commune") {
              const rubrique = ligne.type === "etablissement" ? "Établissements" : "Communes";
              const nom = ligne.type === "etablissement" ? ligne.data.nom : ligne.data.commune;
              const meta =
                ligne.type === "etablissement" ? metaEtablissement(ligne.data) : metaCommune(ligne.data);
              return (
                <div key={id}>
                  {debutSection && (
                    <div className="border-t border-filet/60 px-3.5 pb-1.5 pt-2.5 font-ui text-[10px] font-bold uppercase tracking-[.06em] text-texte-doux first:border-t-0">
                      {rubrique}
                    </div>
                  )}
                  <button
                    id={id}
                    role="option"
                    aria-selected={surbrille}
                    type="button"
                    onMouseEnter={() => setActif(index)}
                    onClick={() => aller(ligne)}
                    className={`flex w-full cursor-pointer items-center gap-2.5 px-3.5 py-2.5 text-left ${
                      surbrille ? "border-l-2 border-action bg-fond-creme pl-3" : ""
                    }`}
                  >
                    {ligne.type === "commune" && (
                      <span
                        aria-hidden
                        className="flex h-6 w-6 flex-none items-center justify-center rounded-[7px] bg-fond-sable text-[12px] text-texte-doux"
                      >
                        ⌂
                      </span>
                    )}
                    <span className="flex-none whitespace-nowrap font-ui text-[13px] text-texte">
                      {surlignerInverse(nom, saisie)}
                    </span>
                    <span className="min-w-0 flex-1 truncate font-ui text-[11.5px] font-medium text-texte-doux">
                      {meta}
                    </span>
                    {surbrille && (
                      <span aria-hidden className="flex-none font-ui text-[10.5px] font-bold text-action">↵</span>
                    )}
                  </button>
                </div>
              );
            }

            if (ligne.type === "voir-tout") {
              return (
                <button
                  key={id}
                  id={id}
                  role="option"
                  aria-selected={surbrille}
                  type="button"
                  onMouseEnter={() => setActif(index)}
                  onClick={() => aller(ligne)}
                  className={`flex w-full cursor-pointer items-center gap-2.5 border-t border-filet/60 px-3.5 py-2.5 text-left font-ui text-[12.5px] font-bold text-action ${
                    surbrille ? "bg-fond-creme" : ""
                  }`}
                >
                  Voir tous les résultats pour « {saisie.trim()} » →
                </button>
              );
            }

            if (ligne.type === "page") {
              return (
                <div key={id}>
                  {debutSection && (
                    <div className="border-t border-filet/60 px-3.5 pb-1.5 pt-2.5 font-ui text-[10px] font-bold uppercase tracking-[.06em] text-texte-doux">
                      Pages
                    </div>
                  )}
                  <button
                    id={id}
                    role="option"
                    aria-selected={surbrille}
                    type="button"
                    onMouseEnter={() => setActif(index)}
                    onClick={() => aller(ligne)}
                    className={`flex w-full cursor-pointer items-center px-3.5 py-2.5 text-left font-ui text-[13px] font-medium text-texte ${
                      surbrille ? "bg-fond-creme" : ""
                    }`}
                  >
                    {ligne.data.titre}
                  </button>
                </div>
              );
            }

            if (ligne.type === "lien-fixe") {
              return (
                <button
                  key={id}
                  id={id}
                  role="option"
                  aria-selected={surbrille}
                  type="button"
                  onMouseEnter={() => setActif(index)}
                  onClick={() => aller(ligne)}
                  className={`flex w-full cursor-pointer items-center justify-between px-3.5 py-2.5 text-left font-ui text-[13px] font-bold text-action ${
                    surbrille ? "bg-fond-creme" : ""
                  }`}
                >
                  {ligne.label} <span aria-hidden>→</span>
                </button>
              );
            }

            // Porte de sortie : reformuler en situation plutôt qu'en nom.
            return (
              <button
                key={id}
                id={id}
                role="option"
                aria-selected={surbrille}
                type="button"
                onMouseEnter={() => setActif(index)}
                onClick={() => aller(ligne)}
                className={`flex w-full cursor-pointer items-center gap-2.5 border-t border-camille px-3.5 py-2.5 text-left ${
                  surbrille ? "bg-camille-pale" : "bg-camille-pale/70"
                }`}
              >
                <GaletAgent taille="mini" />
                <span className="flex-1 whitespace-nowrap font-ui text-[11.5px] font-semibold text-camille-ink">
                  Décrire ma situation à {NOM_ASSISTANT} plutôt qu&apos;un nom
                </span>
                <span aria-hidden className="flex-none font-ui text-[11px] font-bold text-camille-dark">→</span>
              </button>
            );
          })}

          {lignes.length > 0 && (
            <div className="flex items-center gap-3 border-t border-filet/60 bg-fond-carte px-3.5 py-1.5 font-ui text-[9.5px] font-semibold tracking-[.03em] text-filet-fonce">
              <span>↑↓ naviguer</span>
              <span>↵ ouvrir</span>
              <span>esc fermer</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
