"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { NOM_ASSISTANT } from "@/lib/constants";
import { metaEtablissement, metaCommune, surlignerInverse } from "@/lib/rechercheAffichage";
import { construireLignes, hrefLigne, type LigneMenu } from "@/lib/rechercheMenu";
import { useRechercheSuggestions, MIN_CARACTERES } from "@/hooks/useRechercheSuggestions";
import { GaletAgent } from "@/components/GaletAgent";

// Pendant mobile de RechercheChamp : sous md, le champ permanent de la nav
// est masqué (pas la place), remplacé par cette icône qui ouvre une
// recherche plein écran. Même hook, même construireLignes/hrefLigne que
// la version desktop — seule la présentation change (liste plein écran
// au lieu d'un menu ancré de 480 px).

export function RechercheMobile({ hrefAssistant = "/assistant" }: { hrefAssistant?: string }) {
  const router = useRouter();
  const champRef = useRef<HTMLInputElement>(null);

  const { saisie, setSaisie, chargement, etablissements, communes, pages, aucunResultat } =
    useRechercheSuggestions();
  const [ouvert, setOuvert] = useState(false);

  const lignes = construireLignes({ etablissements, communes, pages, aucunResultat });
  const menuActif = saisie.trim().length >= MIN_CARACTERES;

  // Verrouille le scroll de la page derrière l'overlay tant qu'il est ouvert.
  useEffect(() => {
    if (!ouvert) return;
    const precedent = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    champRef.current?.focus();
    return () => {
      document.body.style.overflow = precedent;
    };
  }, [ouvert]);

  function fermer() {
    setOuvert(false);
    setSaisie("");
  }

  function aller(ligne: LigneMenu) {
    fermer();
    router.push(hrefLigne(ligne, saisie.trim(), hrefAssistant));
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOuvert(true)}
        aria-label="Rechercher un collège ou une commune"
        className="flex h-9 w-9 flex-none items-center justify-center rounded-[9px] border border-filet bg-white text-[15px] text-texte-doux outline-none focus-visible:ring-2 focus-visible:ring-action focus-visible:ring-offset-2 md:hidden"
      >
        ⌕
      </button>

      {ouvert && (
        <div className="fixed inset-0 z-50 flex flex-col bg-fond-creme md:hidden">
          <div className="flex flex-none items-center gap-2 border-b border-filet px-4 py-3">
            <div className="flex h-9 flex-1 items-center gap-2 rounded-[9px] border border-action bg-white pl-3 pr-2.5 ring-[3px] ring-action/15">
              <span aria-hidden className="flex-none text-[14px] text-filet-fonce">⌕</span>
              <input
                ref={champRef}
                value={saisie}
                onChange={(e) => setSaisie(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") fermer();
                  else if (e.key === "Enter" && lignes.length > 0) {
                    e.preventDefault();
                    aller(lignes[0]);
                  }
                }}
                placeholder="Rechercher un collège, une commune…"
                aria-label="Rechercher un collège ou une commune"
                className="min-w-0 flex-1 bg-transparent font-ui text-[14px] font-medium text-texte outline-none placeholder:font-medium placeholder:text-filet-fonce"
              />
            </div>
            <button
              type="button"
              onClick={fermer}
              className="flex-none font-ui text-[13px] font-bold text-texte-doux"
            >
              Annuler
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {!menuActif && (
              <div className="px-4 py-4 font-ui text-[13px] text-texte-doux">
                Tapez au moins {MIN_CARACTERES} caractères pour chercher.
              </div>
            )}

            {menuActif && lignes.length === 0 && (
              <div className="px-4 py-4 font-ui text-[13px] text-texte-doux">
                {chargement ? "Recherche en cours…" : "Continuez à taper pour chercher."}
              </div>
            )}

            {aucunResultat && (
              <div className="px-4 pb-2 pt-4 font-ui text-[13px] leading-[1.5] text-texte-doux">
                Aucun résultat pour « {saisie.trim()} ». Vérifiez l&apos;orthographe, ou essayez avec juste
                le nom de la ville.
              </div>
            )}

            {lignes.map((ligne, index) => {
              const precedent = lignes[index - 1];
              const debutSection = precedent === undefined || precedent.type !== ligne.type;

              if (ligne.type === "etablissement" || ligne.type === "commune") {
                const rubrique = ligne.type === "etablissement" ? "Établissements" : "Communes";
                const nom = ligne.type === "etablissement" ? ligne.data.nom : ligne.data.commune;
                const meta =
                  ligne.type === "etablissement" ? metaEtablissement(ligne.data) : metaCommune(ligne.data);
                return (
                  <div key={index}>
                    {debutSection && (
                      <div className="border-t border-filet/60 px-4 pb-1.5 pt-3 font-ui text-[10px] font-bold uppercase tracking-[.06em] text-texte-doux first:border-t-0">
                        {rubrique}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => aller(ligne)}
                      className="flex w-full items-center gap-2.5 px-4 py-3 text-left"
                    >
                      {ligne.type === "commune" && (
                        <span
                          aria-hidden
                          className="flex h-6 w-6 flex-none items-center justify-center rounded-[7px] bg-fond-sable text-[12px] text-texte-doux"
                        >
                          ⌂
                        </span>
                      )}
                      <span className="min-w-0 flex-1">
                        <span className="block font-ui text-[14px] text-texte">
                          {surlignerInverse(nom, saisie)}
                        </span>
                        <span className="block truncate font-ui text-[12px] font-medium text-texte-doux">
                          {meta}
                        </span>
                      </span>
                    </button>
                  </div>
                );
              }

              if (ligne.type === "voir-tout") {
                return (
                  <button
                    key={index}
                    type="button"
                    onClick={() => aller(ligne)}
                    className="w-full border-t border-filet/60 px-4 py-3 text-left font-ui text-[13px] font-bold text-action"
                  >
                    Voir tous les résultats pour « {saisie.trim()} » →
                  </button>
                );
              }

              if (ligne.type === "page") {
                return (
                  <div key={index}>
                    {debutSection && (
                      <div className="border-t border-filet/60 px-4 pb-1.5 pt-3 font-ui text-[10px] font-bold uppercase tracking-[.06em] text-texte-doux">
                        Pages
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => aller(ligne)}
                      className="w-full px-4 py-3 text-left font-ui text-[14px] font-medium text-texte"
                    >
                      {ligne.data.titre}
                    </button>
                  </div>
                );
              }

              if (ligne.type === "lien-fixe") {
                return (
                  <button
                    key={index}
                    type="button"
                    onClick={() => aller(ligne)}
                    className="flex w-full items-center justify-between px-4 py-3 text-left font-ui text-[14px] font-bold text-action"
                  >
                    {ligne.label} <span aria-hidden>→</span>
                  </button>
                );
              }

              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => aller(ligne)}
                  className="flex w-full items-center gap-2.5 border-t border-camille bg-camille-pale/70 px-4 py-3 text-left"
                >
                  <GaletAgent taille="mini" />
                  <span className="flex-1 font-ui text-[12.5px] font-semibold text-camille-ink">
                    Décrire ma situation à {NOM_ASSISTANT} plutôt qu&apos;un nom
                  </span>
                  <span aria-hidden className="flex-none font-ui text-[11px] font-bold text-camille-dark">→</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
