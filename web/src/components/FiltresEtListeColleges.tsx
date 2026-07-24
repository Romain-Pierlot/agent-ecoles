"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CollegeVille } from "@/lib/types";
import { deriveDispositifsEducatifs, deriveSections, SECTION_VERS_CLE_API, CLE_API_VERS_SECTION } from "@/lib/dispositifs";
import { ListeColleges } from "@/components/ListeColleges";
import { SelectFiltre } from "@/components/SelectFiltre";
import { BoutonDirectionTri, type DirectionTri } from "@/components/BoutonDirectionTri";
import type { FiltresEtablissements } from "@/lib/rechercheParams";

// Du plus fort au plus faible — miroir de config.py::NOTATION_LETTRES
// (inversé), qui reste la source de vérité côté back pour le calcul réel de
// la notation. Ici on ne fait que comparer un ordre déjà établi.
const NOTATIONS_ORDRE = ["A+", "A", "A-", "B+", "B"];

type CritereTri = "notation" | "reussite" | "alphabetique";

export function FiltresEtListeColleges({
  colleges,
  tauxReussiteNational,
  modeServeur,
}: {
  // hrefBase porté par chaque collège (pas un prop séparé) : partagé avec
  // /recherche, où chaque résultat peut venir d'une ville différente — la
  // page ville attache le même hrefBase à tous ses collèges avant l'appel,
  // la page recherche attache le hrefBase propre à chacun.
  // commune/libelle_departement/code_departement optionnels sur CollegeVille,
  // toujours présents sur EtablissementRecherche (/recherche) — la page ville
  // les fournit désormais explicitement (cf. ville/page.tsx) ; CarteCollege
  // affiche la ligne de localisation sur les deux pages dès qu'ils sont fournis.
  colleges: (CollegeVille & {
    hrefBase: string;
    commune?: string;
    libelle_departement?: string;
    code_departement?: string;
  })[];
  tauxReussiteNational: number | null;
  // Mode serveur (page /recherche uniquement) : `colleges` est déjà filtré
  // et trié côté API (LIMIT appliqué après filtrage — cf. Phase 6, fix de
  // troncature). Ce composant ne refiltre alors plus localement : il
  // notifie juste le parent à chaque changement de filtre/tri pour qu'il
  // relance l'appel /recherche. Absent (page ville) : filtrage/tri 100%
  // local, comportement inchangé.
  modeServeur?: {
    filtresInitiaux: FiltresEtablissements;
    onFiltresChange: (filtres: FiltresEtablissements) => void;
    nbTotal: number;
    tronque: boolean;
  };
}) {
  const [filtreSecteur, setFiltreSecteur] = useState(modeServeur?.filtresInitiaux.secteur ?? "tous");
  const [filtreDispositif, setFiltreDispositif] = useState(modeServeur?.filtresInitiaux.dispositif ?? "tous");
  const [filtreSection, setFiltreSection] = useState(
    modeServeur?.filtresInitiaux.section ? (CLE_API_VERS_SECTION[modeServeur.filtresInitiaux.section] ?? "toutes") : "toutes"
  );
  const [notationMin, setNotationMin] = useState(modeServeur?.filtresInitiaux.notationMin ?? "toutes");
  const [critereTri, setCritereTri] = useState<CritereTri>(modeServeur?.filtresInitiaux.tri ?? "notation");
  const [directionTri, setDirectionTri] = useState<DirectionTri>(modeServeur?.filtresInitiaux.direction ?? "desc");

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

  // Notifie le parent en mode serveur à chaque changement de filtre/tri —
  // sauf au premier rendu (les valeurs initiales viennent déjà du fetch
  // initial fait par le parent, un second appel identique serait inutile).
  const premierRendu = useRef(true);
  useEffect(() => {
    if (!modeServeur) return;
    if (premierRendu.current) {
      premierRendu.current = false;
      return;
    }
    modeServeur.onFiltresChange({
      secteur: filtreSecteur === "tous" ? null : (filtreSecteur as FiltresEtablissements["secteur"]),
      dispositif: filtreDispositif === "tous" ? null : (filtreDispositif as FiltresEtablissements["dispositif"]),
      section: filtreSection === "toutes" ? null : ((SECTION_VERS_CLE_API[filtreSection] as FiltresEtablissements["section"]) ?? null),
      notationMin: notationMin === "toutes" ? null : (notationMin as FiltresEtablissements["notationMin"]),
      tri: critereTri,
      direction: directionTri,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtreSecteur, filtreDispositif, filtreSection, notationMin, critereTri, directionTri]);

  const resultats = useMemo(() => {
    if (modeServeur) return colleges; // déjà filtré/trié côté API, rien à refaire ici

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
      if (critereTri === "alphabetique") {
        const diff = a.nom.localeCompare(b.nom);
        return directionTri === "asc" ? diff : -diff;
      }
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
  }, [colleges, modeServeur, filtreSecteur, filtreDispositif, filtreSection, notationMin, critereTri, directionTri]);

  const nbResultats = modeServeur ? modeServeur.nbTotal : resultats.length;
  const resultatsTronques = modeServeur?.tronque ?? false;

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
          {nbResultats} résultat{nbResultats > 1 ? "s" : ""}
          {resultatsTronques && (
            <span className="ml-1.5 font-semibold text-texte-doux/70">(affichage limité à {colleges.length})</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-texte-doux">
          <span>Trier :</span>
          <SelectFiltre value={critereTri} onChange={(v) => setCritereTri(v as CritereTri)} actif={false}>
            <option value="notation">Notation</option>
            <option value="reussite">Réussite</option>
            <option value="alphabetique">Alphabétique</option>
          </SelectFiltre>
          <BoutonDirectionTri
            direction={directionTri}
            onToggle={() => setDirectionTri((d) => (d === "desc" ? "asc" : "desc"))}
          />
        </div>
      </div>

      {resultats.length === 0 ? (
        <div className="mt-2.5 rounded-[13px] border-[1.5px] border-dashed border-filet-fonce py-6 text-center text-[12.5px] font-semibold text-texte-doux">
          Aucun collège ne correspond à ces filtres.
        </div>
      ) : (
        <ListeColleges
          colleges={resultats}
          tauxReussiteNational={tauxReussiteNational}
          critereTriActif={critereTri === "alphabetique" ? undefined : critereTri}
        />
      )}
    </>
  );
}
