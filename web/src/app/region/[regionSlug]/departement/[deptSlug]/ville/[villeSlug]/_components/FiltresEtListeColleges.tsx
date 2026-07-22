"use client";

import { useMemo, useState } from "react";
import type { CollegeVille } from "@/lib/types";
import { deriveDispositifsEducatifs, deriveSections } from "@/lib/dispositifs";
import { ListeColleges } from "@/components/ListeColleges";

// Du plus fort au plus faible — miroir de config.py::NOTATION_LETTRES
// (inversé), qui reste la source de vérité côté back pour le calcul réel de
// la notation. Ici on ne fait que comparer un ordre déjà établi.
const NOTATIONS_ORDRE = ["A+", "A", "A-", "B+", "B"];

type CritereTri = "notation" | "reussite";
type DirectionTri = "asc" | "desc";

function classesFiltre(actif: boolean): string {
  return actif
    ? "border-[1.5px] border-[#E9A9C0] bg-action-pale text-action-dark"
    : "border-[1.5px] border-filet bg-white text-texte-doux";
}

function SelectFiltre({
  value,
  onChange,
  actif,
  children,
}: {
  value: string;
  onChange: (v: string) => void;
  actif: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={`relative rounded-[9px] ${classesFiltre(actif)}`}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-transparent py-1.5 pl-2.5 pr-6 text-[11px] font-bold outline-none"
      >
        {children}
      </select>
      <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[9px]">▾</span>
    </div>
  );
}

export function FiltresEtListeColleges({
  colleges,
  hrefBase,
  tauxReussiteNational,
}: {
  colleges: CollegeVille[];
  hrefBase: string;
  tauxReussiteNational: number | null;
}) {
  const [filtreSecteur, setFiltreSecteur] = useState("tous");
  const [filtreDispositif, setFiltreDispositif] = useState("tous");
  const [filtreSection, setFiltreSection] = useState("toutes");
  const [notationMin, setNotationMin] = useState("toutes");
  const [critereTri, setCritereTri] = useState<CritereTri>("notation");
  const [directionTri, setDirectionTri] = useState<DirectionTri>("desc");

  const optionsDispositifs = useMemo(() => {
    const set = new Set<string>();
    colleges.forEach((c) => deriveDispositifsEducatifs(c).forEach((d) => set.add(d)));
    return Array.from(set).sort();
  }, [colleges]);

  const optionsSections = useMemo(() => {
    const set = new Set<string>();
    colleges.forEach((c) => deriveSections(c).forEach((s) => set.add(s)));
    return Array.from(set).sort();
  }, [colleges]);

  const resultats = useMemo(() => {
    let liste = colleges;
    if (filtreSecteur !== "tous") liste = liste.filter((c) => c.secteur === filtreSecteur);
    if (filtreDispositif !== "tous") {
      liste = liste.filter((c) => deriveDispositifsEducatifs(c).includes(filtreDispositif));
    }
    if (filtreSection !== "toutes") {
      liste = liste.filter((c) => deriveSections(c).includes(filtreSection));
    }
    if (notationMin !== "toutes") {
      const rangMin = NOTATIONS_ORDRE.indexOf(notationMin);
      liste = liste.filter((c) => c.notation !== null && NOTATIONS_ORDRE.indexOf(c.notation) <= rangMin);
    }

    // Les collèges sans donnée (notation ou réussite absente) restent
    // toujours en dernier, quel que soit le sens choisi — une donnée
    // manquante n'est ni "la meilleure" ni "la pire", inverser le sens ne
    // doit pas la faire remonter en tête.
    return [...liste].sort((a, b) => {
      if (critereTri === "reussite") {
        const ta = a.brevet_taux_reussite_general;
        const tb = b.brevet_taux_reussite_general;
        if (ta === null && tb === null) return 0;
        if (ta === null) return 1;
        if (tb === null) return -1;
        const diff = tb - ta;
        return directionTri === "asc" ? -diff : diff;
      }
      const rangA = a.notation ? NOTATIONS_ORDRE.indexOf(a.notation) : null;
      const rangB = b.notation ? NOTATIONS_ORDRE.indexOf(b.notation) : null;
      if (rangA === null && rangB === null) return a.nom.localeCompare(b.nom);
      if (rangA === null) return 1;
      if (rangB === null) return -1;
      if (rangA !== rangB) {
        const diff = rangA - rangB;
        return directionTri === "asc" ? -diff : diff;
      }
      return a.nom.localeCompare(b.nom);
    });
  }, [colleges, filtreSecteur, filtreDispositif, filtreSection, notationMin, critereTri, directionTri]);

  // hrefBase attaché à chaque collège : ListeColleges est partagée avec
  // /recherche, où chaque résultat peut venir d'une ville différente — ici
  // c'est toujours le même hrefBase, répété pour respecter ce contrat.
  const resultatsAvecHref = useMemo(
    () => resultats.map((c) => ({ ...c, hrefBase })),
    [resultats, hrefBase]
  );

  return (
    <>
      {/* ===== BARRE DE FILTRES ===== */}
      <div className="mt-3.5 flex flex-wrap items-center gap-2">
        <span className="mr-0.5 text-[10px] font-bold uppercase tracking-wide text-texte-doux">Filtrer</span>

        <SelectFiltre value={filtreSecteur} onChange={setFiltreSecteur} actif={filtreSecteur !== "tous"}>
          <option value="tous">Public / Privé</option>
          <option value="Public">Public</option>
          <option value="Privé">Privé</option>
        </SelectFiltre>

        {optionsDispositifs.length > 0 && (
          <SelectFiltre value={filtreDispositif} onChange={setFiltreDispositif} actif={filtreDispositif !== "tous"}>
            <option value="tous">Dispositifs</option>
            {optionsDispositifs.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </SelectFiltre>
        )}

        {optionsSections.length > 0 && (
          <SelectFiltre value={filtreSection} onChange={setFiltreSection} actif={filtreSection !== "toutes"}>
            <option value="toutes">Sections</option>
            {optionsSections.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </SelectFiltre>
        )}

        <SelectFiltre value={notationMin} onChange={setNotationMin} actif={notationMin !== "toutes"}>
          <option value="toutes">Notation min.</option>
          {NOTATIONS_ORDRE.map((n) => (
            <option key={n} value={n}>{n} et plus</option>
          ))}
        </SelectFiltre>
      </div>

      {/* ===== TRI + RÉSULTATS ===== */}
      <div className="mt-3.5 flex items-center justify-between">
        <div className="text-[12px] font-bold text-texte-doux">
          {resultats.length} résultat{resultats.length > 1 ? "s" : ""}
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-texte-doux">
          <span>Trier :</span>
          <SelectFiltre value={critereTri} onChange={(v) => setCritereTri(v as CritereTri)} actif={false}>
            <option value="notation">Notation</option>
            <option value="reussite">Réussite</option>
          </SelectFiltre>
          <button
            type="button"
            onClick={() => setDirectionTri((d) => (d === "desc" ? "asc" : "desc"))}
            className="flex h-[26px] w-[26px] flex-none items-center justify-center rounded-[9px] border-[1.5px] border-filet bg-white text-[12px] text-texte-doux hover:border-filet-fonce"
            title={
              directionTri === "desc"
                ? "Ordre décroissant — cliquer pour inverser"
                : "Ordre croissant — cliquer pour inverser"
            }
          >
            {directionTri === "desc" ? "↓" : "↑"}
          </button>
        </div>
      </div>

      {resultatsAvecHref.length === 0 ? (
        <div className="mt-2.5 rounded-[13px] border-[1.5px] border-dashed border-filet-fonce py-6 text-center text-[12.5px] font-semibold text-texte-doux">
          Aucun collège ne correspond à ces filtres.
        </div>
      ) : (
        <ListeColleges
          colleges={resultatsAvecHref}
          tauxReussiteNational={tauxReussiteNational}
          critereTriActif={critereTri}
        />
      )}
    </>
  );
}
