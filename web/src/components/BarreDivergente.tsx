// Barre divergente centrée sur zéro, utilisée par la colonne "Écart à
// l'attendu" des tableaux de sous-divisions (SousDivisionsTable) — jamais
// sur les cartes établissement individuelles (cf. décision : les barres ne
// fonctionnent que dans un tableau où les lignes s'alignent verticalement).

// Échelle fixe, identique sur toutes les pages hub pour rester comparable
// d'une page à l'autre — au-delà, la barre est pleine mais le chiffre à
// côté reste exact (ex: Guyane, +17,1 avec une barre pleine à droite).
const ECHELLE_MAX = 8;

export function BarreDivergente({ valeur }: { valeur: number }) {
  const positif = valeur >= 0;
  const largeurPct = Math.min(Math.abs(valeur) / ECHELLE_MAX, 1) * 50;

  return (
    <div aria-hidden className="relative h-4 w-full overflow-hidden rounded-md bg-fond-sable">
      <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-filet-fonce" />
      <div
        className={`absolute top-0 h-full rounded-[3px] ${positif ? "bg-positif" : "bg-attention"}`}
        style={positif ? { left: "50%", width: `${largeurPct}%` } : { right: "50%", width: `${largeurPct}%` }}
      />
    </div>
  );
}
