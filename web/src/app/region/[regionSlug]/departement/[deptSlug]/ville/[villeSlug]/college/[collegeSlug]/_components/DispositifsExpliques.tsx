import type { EtablissementIdentite } from "@/lib/types";

// Pas de couleur sémantique par dispositif ici — la convention de couleur
// pour REP+/ULIS/SEGPA (et plus largement les badges de dispositifs/sections)
// reste un point ouvert, volontairement laissé au backlog plutôt que décidé
// à la volée. Un seul style neutre en attendant, cohérent avec les badges de
// la carte identité.
const CLASSE_BADGE_NEUTRE = "bg-fond-sable/60 text-texte-doux";

const EXPLICATIONS: { cle: string; test: (i: EtablissementIdentite) => boolean; badge: string; titre: string; texte: string }[] = [
  {
    cle: "education-prioritaire",
    test: (i) => Boolean(i.appartenance_education_prioritaire),
    badge: "", // remplacé dynamiquement par la valeur réelle (REP/REP+)
    titre: "Réseau d'éducation prioritaire",
    texte:
      "Moyens supplémentaires (classes allégées, accompagnement) pour les collèges de quartiers plus fragiles socialement. REP+ désigne les situations les plus marquées, REP les situations intermédiaires.",
  },
  {
    cle: "ulis",
    test: (i) => i.ulis,
    badge: "ULIS",
    titre: "Unité localisée pour l'inclusion scolaire",
    texte: "Une classe qui accueille des élèves en situation de handicap, intégrés au maximum aux cours ordinaires.",
  },
  {
    cle: "segpa",
    test: (i) => i.segpa,
    badge: "SEGPA",
    titre: "Section d'enseignement adapté",
    texte:
      "Pour les élèves en grande difficulté scolaire : petits effectifs, rythme adapté, et une forte dimension pré-professionnelle.",
  },
];

export function DispositifsExpliques({ identite }: { identite: EtablissementIdentite }) {
  const cartes = EXPLICATIONS.filter((e) => e.test(identite));
  if (cartes.length === 0) return null;

  return (
    <div id="dispositifs" className="mt-11 scroll-mt-28">
      <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-action">Comprendre, sans jargon</div>
      <h2 className="font-baloo text-[25px] font-extrabold text-texte">Les dispositifs de ce collège, expliqués</h2>
      <div className="mt-4 grid gap-3.5 sm:grid-cols-3">
        {cartes.map((c) => (
          <div key={c.cle} className="rounded-[18px] border-2 border-filet bg-white p-[18px_20px]">
            <span className={`rounded-lg px-2.5 py-1 text-[11px] font-bold ${CLASSE_BADGE_NEUTRE}`}>
              {c.cle === "education-prioritaire" ? identite.appartenance_education_prioritaire : c.badge}
            </span>
            <div className="mt-2.5 font-baloo text-[14.5px] font-bold text-texte">{c.titre}</div>
            <p className="mt-1.5 text-[12px] leading-relaxed text-texte-doux">{c.texte}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
