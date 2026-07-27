import Link from "next/link";

// Refonte terracotta (cf. handoff design homepage, section 7 · Footer) :
// fond sombre à colonnes, remplace l'ancien footer minimal clair à liens
// plats. Deux colonnes du brief original ("Mise à jour", "Code source
// GitHub"/"Signaler une erreur") retirées : aucune métadonnée réelle de
// date de dernière ingestion dans le projet, et aucun dépôt public ni canal
// de signalement confirmés — inventer ces informations aurait été trompeur
// pour un vrai produit en production (cf. decision_log.md).
//
// La colonne "Ouvert" reprend tous les liens de l'ancien footer (pas
// seulement "Mentions légales" du brief) : ce composant est global, partagé
// par toutes les pages du site — /calendrier-scolaire et /sources n'ont pas
// d'autre point d'entrée navigable ailleurs sur la plupart des pages.
const LIENS_OUVERT: { href: string; label: string }[] = [
  { href: "/calendrier-scolaire", label: "Calendrier scolaire" },
  { href: "/methodologie", label: "Notre méthode" },
  { href: "/sources", label: "Sources & données" },
  { href: "/a-propos", label: "À propos" },
  { href: "/mentions-legales", label: "Mentions légales" },
];

function TitreColonne({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-ui text-[10.5px] font-bold uppercase tracking-[0.12em] text-[#C4B79F]">
      {children}
    </div>
  );
}

export function Footer() {
  return (
    <footer className="mt-auto bg-[#201C17]">
      <div className="mx-auto grid max-w-[1280px] grid-cols-2 gap-x-6 gap-y-7 px-4 py-9 md:grid-cols-[1.3fr_1fr_1fr] md:gap-x-[34px] md:px-[50px] md:py-11">
        <div className="col-span-2 md:col-span-1">
          <TitreColonne>Sources</TitreColonne>
          <div className="mt-2.5 font-ui text-[12.5px] leading-[1.85] text-[#E4DDCE]">
            Ministère de l&apos;Éducation nationale (DEPP)
            <br />
            Base Adresse Nationale
            <br />
            IGN
            <br />
            Conseils départementaux (sectorisation)
          </div>
        </div>

        <div>
          <TitreColonne>Session des données</TitreColonne>
          <div className="mt-2.5 font-ui text-[12.5px] leading-[1.85] text-[#E4DDCE]">
            Brevet · session 2025
            <br />
            IPS · rentrée 2025
            <br />
            Sectorisation · 2025
          </div>
        </div>

        <div>
          <TitreColonne>Ouvert</TitreColonne>
          <div className="mt-2.5 flex flex-col items-start gap-1.5">
            {LIENS_OUVERT.map((lien) => (
              <Link
                key={lien.href}
                href={lien.href}
                className="border-b border-[#4A4238] pb-0.5 font-ui text-[12.5px] font-medium text-[#E4DDCE] hover:text-white"
              >
                {lien.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
