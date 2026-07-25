// Icône de Camille : forme "galet" retenue dans les tours de décision du
// design (tours 4-8, variante 8b) - jamais un rond avec une lettre. Corps
// arrondi asymétrique (un seul coin net), dégradé apricot -> terracotta
// brun, 3 points blancs dégressifs (façon indicateur de frappe). Deux
// tailles fidèles à la maquette (tour 9/11/12) : "mini" dans les CTA de nav,
// "carte" dans les blocs Camille (AgentBlock, fiche établissement...).
const TAILLES = {
  mini: { largeur: 24, hauteur: 22, coinNet: 7, dot: 3.5, gap: 2.5, ombre: "0 2px 6px rgba(192,81,46,.28)" },
  carte: { largeur: 38, hauteur: 35, coinNet: 11, dot: 5, gap: 3, ombre: "0 4px 11px rgba(192,81,46,.28)" },
} as const;

export function GaletCamille({ taille = "carte" }: { taille?: keyof typeof TAILLES }) {
  const t = TAILLES[taille];
  return (
    <div
      className="flex flex-none items-center justify-center"
      style={{
        width: t.largeur,
        height: t.hauteur,
        gap: t.gap,
        borderRadius: `44% 44% 44% ${t.coinNet}px`,
        background: "linear-gradient(150deg,#EFB85A,#C0512E)",
        boxShadow: t.ombre,
      }}
    >
      {[1, 0.72, 0.46].map((opacite, i) => (
        <span
          key={i}
          className="rounded-full bg-[#FFF7E6]"
          style={{ width: t.dot, height: t.dot, opacity: opacite }}
        />
      ))}
    </div>
  );
}
