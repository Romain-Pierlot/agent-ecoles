import Link from "next/link";
import { CATEGORIES, type Categorie } from "@/lib/comprendre";

// Rail à double fonction (cf. bundle design_handoff_comprendre, §3) :
// navigateur de catégories sur l'index et le glossaire, sommaire de page
// sur un guide. Les deux modes ne partagent pas d'anatomie visuelle, donc
// pas de props communes forcées au-delà du conteneur sticky.

type RailNavigateur = {
  mode: "navigateur";
  // Lien de retour affiché au-dessus des catégories : utilisé sur le
  // glossaire ("‹ Comprendre"), absent sur l'index (rien au-dessus).
  retour?: { label: string; href: string };
  // Catégorie de la page courante : déplie ses ancres "Aller à" (règle A du
  // bundle). Sur l'index, laissé vide au lancement (pas de suivi de scroll
  // pour l'instant) — à revisiter si le besoin se confirme à l'usage.
  categorieActive?: Categorie;
  comptes: Partial<Record<Categorie["slug"], number>>;
  // Le libellé/lien/compte du glossaire varient selon le contexte : "Glossaire"
  // (total) sur l'index, "Glossaire de la catégorie" (compte filtré) sur une
  // page catégorie. Absent sur le glossaire lui-même (pas de lien vers la
  // page courante) — cf. bundle, écrans 22a, 24b et 26a.
  glossaire?: { label: string; href: string; compte: number };
};

type RailSommaire = {
  mode: "sommaire";
  retour: { label: string; href: string };
  sections: { titre: string; ancre: string }[];
};

export function RailComprendre(props: RailNavigateur | RailSommaire) {
  if (props.mode === "sommaire") {
    const { retour, sections } = props;
    // Repliée en dépliant sous le chapeau côté mobile (cf. bundle, écran
    // 25b) : ce rail-ci ne s'affiche qu'à partir de md, pas de doublon.
    return (
      <div className="sticky top-[76px] hidden flex-col gap-1 md:flex">
        <Link
          href={retour.href}
          className="inline-flex items-center gap-1.5 pb-3.5 font-ui text-[12.5px] font-semibold text-action-dark"
        >
          ‹ {retour.label}
        </Link>
        <div className="px-3 pb-2.5 font-ui text-[11px] font-bold tracking-[.09em] text-texte-doux uppercase">
          Sur cette page
        </div>
        {sections.map((section) => (
          <a
            key={section.ancre}
            href={`#${section.ancre}`}
            className="rounded-lg px-3 py-2 font-ui text-[13px] font-medium text-texte-doux hover:bg-fond-carte"
          >
            {section.titre}
          </a>
        ))}
      </div>
    );
  }

  const { retour, categorieActive, comptes, glossaire } = props;

  return (
    <>
      {/* Mobile (< md) : rangée de pastilles collante sous l'en-tête, mêmes
          catégories/ordre/comptes, libellés raccourcis (cf. bundle, §6). */}
      <div className="sticky top-14 z-30 -mx-4.5 flex gap-2 overflow-x-auto border-y border-filet bg-fond-creme px-4.5 py-2.5 md:hidden">
        {CATEGORIES.map((categorie) => {
          const active = categorieActive?.slug === categorie.slug;
          return (
            <Link
              key={categorie.slug}
              href={`/comprendre/${categorie.slug}`}
              className={`flex-none rounded-full px-3.5 py-3 font-ui text-[13px] font-bold whitespace-nowrap ${
                active ? "bg-action text-white" : "border border-filet-fonce bg-fond-carte text-texte"
              }`}
            >
              {categorie.labelMobile ?? categorie.label} {comptes[categorie.slug] ?? 0}
            </Link>
          );
        })}
      </div>

      {/* Desktop (>= md) : rail vertical complet. */}
      <div className="sticky top-[76px] hidden flex-col gap-1 md:flex">
        {retour && (
          <Link
            href={retour.href}
            className="inline-flex items-center gap-1.5 pb-3.5 font-ui text-[12.5px] font-semibold text-action-dark"
          >
            ‹ {retour.label}
          </Link>
        )}
        <div className="px-3 pb-2.5 font-ui text-[11px] font-bold tracking-[.09em] text-texte-doux uppercase">
          Catégories
        </div>
        {CATEGORIES.map((categorie) => {
          const active = categorieActive?.slug === categorie.slug;
          return (
            <div key={categorie.slug}>
              <Link
                href={`/comprendre/${categorie.slug}`}
                className={`flex items-center justify-between gap-2.5 rounded-[9px] px-3 py-2.5 font-ui text-[14px] font-semibold text-texte ${
                  active ? "bg-rail-actif" : ""
                }`}
              >
                <span>{categorie.label}</span>
                <span className={`font-ui text-[12px] font-bold ${active ? "text-action-dark" : "text-texte-doux"}`}>
                  {comptes[categorie.slug] ?? 0}
                </span>
              </Link>
              {active && categorie.sousThemes && (
                <div className="mt-1 mb-2 ml-5.5 flex flex-col gap-0.5 border-l-2 border-filet pl-2.5">
                  <div className="pt-0.5 pb-1 font-ui text-[10px] font-bold tracking-[.09em] text-texte-doux uppercase">
                    Aller à
                  </div>
                  {categorie.sousThemes.map((sousTheme) => (
                    <a
                      key={sousTheme}
                      href={`#${sousTheme}`}
                      className="py-1 font-ui text-[12.5px] font-medium text-texte-doux hover:text-action-dark"
                    >
                      {sousTheme}
                    </a>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        <div className="my-3.5 h-px bg-filet-fonce" />

        <Link
          href="/comprendre/methodologie"
          className="flex items-center gap-2.5 rounded-[9px] px-3 py-2.5 font-ui text-[14px] font-semibold text-texte"
        >
          <span className="h-1.5 w-1.5 flex-none rounded-full bg-methode-accent" />
          Méthodologie du site
        </Link>
        {glossaire && (
          <Link
            href={glossaire.href}
            className="flex items-center justify-between gap-2.5 rounded-[9px] px-3 py-2.5 font-ui text-[14px] font-semibold text-texte"
          >
            <span>{glossaire.label}</span>
            <span className="font-ui text-[12px] font-bold text-texte-doux">{glossaire.compte}</span>
          </Link>
        )}
      </div>
    </>
  );
}
