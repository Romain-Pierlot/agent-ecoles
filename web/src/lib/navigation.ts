// Liens de navigation principaux du header — factorisés ici car partagés
// entre TopBar (nav desktop) et MenuMobile (overlay mobile) : un seul
// endroit à mettre à jour si un lien change.

export type LienNav = { href: string; label: string; match?: string };

export const LIENS_NAV: LienNav[] = [
  { href: "/carte-scolaire", label: "Mon collège de secteur" },
  { href: "/explorer", label: "Explorer" },
  { href: "/comprendre/ips", label: "Comprendre", match: "/comprendre" },
];
