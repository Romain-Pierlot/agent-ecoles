import { decomposerDate } from "@/lib/formatDateLongue";

// "1ᵉʳ" toujours composé 1 + <sup>er</sup> (cf. README du handoff design).
function JourDuMois({ jour }: { jour: number }) {
  if (jour !== 1) return <>{jour}</>;
  return (
    <>
      1<sup className="text-[.6em]">er</sup>
    </>
  );
}

// Nom du jour en minuscules sauf en début de chaîne (ex: "Mardi 1ᵉʳ
// septembre 2026" seul dans une cellule, mais "Du samedi ... au lundi ..."
// quand il est enchaîné dans PeriodePlage) — capitaliser=true pour le
// premier cas, cf. README §Contenu du tableau.
export function DateLongue({ iso, capitaliser = false }: { iso: string; capitaliser?: boolean }) {
  const { jourSemaine, jour, mois, annee } = decomposerDate(iso);
  const jourAffiche = capitaliser ? jourSemaine[0].toUpperCase() + jourSemaine.slice(1) : jourSemaine;
  return (
    <>
      {jourAffiche} <JourDuMois jour={jour} /> {mois} {annee}
    </>
  );
}

// Une période "vacances" (date_fin non nulle) devient "Du samedi X au lundi
// Y" avec un saut de ligne entre les deux, un jalon (date_fin nulle) reste
// une date seule capitalisée — cf. README §Contenu du tableau.
export function PeriodePlage({ dateDebut, dateFin }: { dateDebut: string; dateFin: string | null }) {
  if (!dateFin) {
    return <DateLongue iso={dateDebut} capitaliser />;
  }
  return (
    <>
      Du <DateLongue iso={dateDebut} />
      <br />
      au <DateLongue iso={dateFin} />
    </>
  );
}
