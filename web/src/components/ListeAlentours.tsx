import { CarteCollege } from "@/components/CarteCollege";
import { hrefBaseVille } from "@/lib/hrefsGeo";
import type { CollegeSecteurItem } from "@/lib/types";

// Bandeau partagé par la page carte scolaire (repli "alentours" des 3 états
// géocodés, collèges déjà dédupliqués contre colleges_secteur côté backend,
// cf. agent/tools/carte_scolaire_tool.py::resoudre_secteur) et la fiche
// établissement (3 collèges les plus proches, cf.
// agent/tools/etablissement_tool.py::_obtenir_etablissements_proches).
export function ListeAlentours({
  colleges,
  titre,
  sousTitre,
}: {
  colleges: CollegeSecteurItem[];
  titre: string;
  sousTitre?: string;
}) {
  if (colleges.length === 0) return null;

  return (
    <div className="mt-6.5">
      <div className="mb-1 text-[11px] font-bold uppercase tracking-[0.06em] text-action">{titre}</div>
      {sousTitre && <p className="mb-2.5 text-[12px] leading-relaxed text-texte-doux">{sousTitre}</p>}
      <div className="mt-2.5 flex flex-col gap-2">
        {colleges.map((college) => (
          <CarteCollege
            key={college.uai}
            college={college}
            hrefBase={hrefBaseVille(college)}
            distanceKm={college.distance_km}
          />
        ))}
      </div>
    </div>
  );
}
