import Link from "next/link";

type Props = {
  titre: string;
  chemin: string;
  params?: Record<string, string>;
};

const LIENS_SQUELETTE: { label: string; href: string }[] = [
  { label: "Accueil", href: "/" },
  { label: "Assistant", href: "/assistant" },
  { label: "Recherche", href: "/recherche" },
  { label: "Explorer", href: "/explorer" },
  { label: "Comprendre (exemple : IPS)", href: "/comprendre/ips" },
  { label: "Régions (liste)", href: "/region" },
  {
    label: "Région (exemple : Auvergne-Rhône-Alpes)",
    href: "/region/auvergne-rhone-alpes",
  },
  {
    label: "Département (exemple : Rhône)",
    href: "/region/auvergne-rhone-alpes/departement/69-rhone",
  },
  {
    label: "Ville (exemple : Lyon)",
    href: "/region/auvergne-rhone-alpes/departement/69-rhone/ville/lyon",
  },
  {
    label: "Fiche établissement (exemple : Jean Moulin)",
    href: "/region/auvergne-rhone-alpes/departement/69-rhone/ville/lyon/college/college-jean-moulin-0692696f",
  },
  { label: "Académie (exemple : Lyon)", href: "/academie/lyon" },
  { label: "Calendrier scolaire", href: "/calendrier" },
  { label: "Notre méthode", href: "/methodologie" },
  { label: "Sources & données", href: "/sources" },
  { label: "À propos", href: "/a-propos" },
  { label: "Mentions légales", href: "/mentions-legales" },
];

export function PagePlaceholder({ titre, chemin, params }: Props) {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
        Squelette de route — à concevoir
      </p>
      <h1 className="mt-2 text-2xl font-bold text-gray-900">{titre}</h1>
      <p className="mt-1 font-mono text-sm text-gray-400">{chemin}</p>

      {params && Object.keys(params).length > 0 && (
        <dl className="mt-6 space-y-1 text-sm text-gray-600">
          {Object.entries(params).map(([cle, valeur]) => (
            <div key={cle} className="flex gap-2">
              <dt className="font-mono text-gray-400">{cle} :</dt>
              <dd className="font-mono">{valeur}</dd>
            </div>
          ))}
        </dl>
      )}

      <nav className="mt-10 border-t border-gray-200 pt-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
          Navigation du squelette
        </p>
        <ul className="space-y-1.5 text-sm">
          {LIENS_SQUELETTE.map((lien) => (
            <li key={lien.href}>
              <Link href={lien.href} className="text-blue-600 hover:underline">
                {lien.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </main>
  );
}
