import Link from "next/link";

// Footer minimal : juste de quoi porter les pages secondaires déjà
// squelettées (cf. PagePlaceholder.tsx) vers un point d'entrée réel. Pas le
// footer complet du design system (fond sombre, colonnes) — hors périmètre
// de cette tâche, à concevoir séparément le jour où il y aura plus de liens
// à y mettre.
const LIENS_FOOTER: { href: string; label: string }[] = [
  { href: "/calendrier-scolaire", label: "Calendrier scolaire" },
  { href: "/methodologie", label: "Notre méthode" },
  { href: "/sources", label: "Sources & données" },
  { href: "/a-propos", label: "À propos" },
  { href: "/mentions-legales", label: "Mentions légales" },
];

export function Footer() {
  return (
    <footer className="mt-auto border-t border-filet bg-fond-carte">
      <div className="mx-auto flex max-w-6xl flex-wrap gap-x-6 gap-y-2 px-4 py-6 font-ui text-[12.5px] font-semibold text-texte-doux md:px-8">
        {LIENS_FOOTER.map((lien) => (
          <Link key={lien.href} href={lien.href} className="hover:text-texte hover:underline">
            {lien.label}
          </Link>
        ))}
      </div>
    </footer>
  );
}
