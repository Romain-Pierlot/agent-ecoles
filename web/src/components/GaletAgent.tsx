// Icône de l'agent conversationnel : forme "galet" retenue dans les tours
// de décision du design (tours 4-8, variante 8b) - jamais un rond avec une
// lettre. Corps arrondi asymétrique (un seul coin net), dégradé apricot ->
// terracotta brun, 3 points blancs dégressifs (façon indicateur de frappe).
// Deux tailles fidèles à la maquette (tour 9/11/12) : "mini" dans les CTA
// de nav, "carte" dans les blocs agent (AgentBlock, fiche établissement...).
const TAILLES = {
  mini: { largeur: 24, hauteur: 22, coinNet: 7, dot: 3.5, gap: 2.5, ombre: "0 2px 6px rgba(201,125,20,.28)" },
  carte: { largeur: 38, hauteur: 35, coinNet: 11, dot: 5, gap: 3, ombre: "0 4px 11px rgba(201,125,20,.28)" },
} as const;

export function GaletAgent({ taille = "carte" }: { taille?: keyof typeof TAILLES }) {
  const t = TAILLES[taille];
  return (
    <div
      className="flex flex-none items-center justify-center"
      /* eslint-disable no-restricted-syntax -- couleurs propres à l'icône du
         galet, registre de référence (docs/Design_system/REFERENCE.md
         section 2), pas des tokens partagés réutilisables ailleurs */
      style={{
        width: t.largeur,
        height: t.hauteur,
        gap: t.gap,
        borderRadius: `44% 44% 44% ${t.coinNet}px`,
        background: "linear-gradient(150deg,#E79A2C,#C97D14)",
        boxShadow: t.ombre,
      }}
    >
      {[1, 0.72, 0.46].map((opacite, i) => (
        <span
          key={i}
          className="rounded-full bg-fond-carte"
          style={{ width: t.dot, height: t.dot, opacity: opacite }}
        />
      ))}
      {/* eslint-enable no-restricted-syntax */}
    </div>
  );
}
