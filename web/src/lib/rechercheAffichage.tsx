import type { EtablissementRecherche, CommuneRecherche } from "@/lib/types";
import { normaliser } from "@/lib/pagesRecherche";

// Formatage partagé entre RechercheChamp (desktop) et RechercheMobile
// (overlay plein écran) — même ligne « meta » et même surlignage des deux
// côtés, un seul endroit à faire évoluer si le format change.

export function metaEtablissement(e: EtablissementRecherche): string {
  return `${e.commune} · ${e.libelle_departement} (${e.code_departement}) · ${e.secteur}`;
}

export function metaCommune(c: CommuneRecherche): string {
  const suffixe = c.nb_etablissements > 1 ? "collèges" : "collège";
  return `${c.libelle_departement} (${c.code_departement}) · ${c.nb_etablissements} ${suffixe}`;
}

/** Surlignage inversé (règle tour 14, non négociable) : ce que le parent a
 * tapé reste en poids normal, le reste du libellé passe en gras — l'œil
 * lit ce qu'il reste à lire, pas ce qui a déjà été saisi. */
export function surlignerInverse(libelle: string, saisie: string) {
  const i = normaliser(libelle).indexOf(normaliser(saisie.trim()));
  if (!saisie.trim() || i < 0) return <span className="font-extrabold">{libelle}</span>;
  const fin = i + saisie.trim().length;
  return (
    <>
      {i > 0 && <span className="font-extrabold">{libelle.slice(0, i)}</span>}
      <span className="font-medium">{libelle.slice(i, fin)}</span>
      {fin < libelle.length && <span className="font-extrabold">{libelle.slice(fin)}</span>}
    </>
  );
}
