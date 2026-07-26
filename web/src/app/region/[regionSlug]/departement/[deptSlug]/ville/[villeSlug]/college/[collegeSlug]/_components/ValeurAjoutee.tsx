import type { ValeurAjouteeDetail } from "@/lib/types";
import { formaterDecimale, formaterPourcentage } from "@/lib/format";

function CarteVa({ titre, attendu, obtenu, unite }: { titre: string; attendu: number; obtenu: number; unite: string }) {
  const ecart = obtenu - attendu;
  const positif = ecart >= 0;
  // Un écart entre deux valeurs se note en points ("+4 pts"), y compris
  // quand les valeurs elles-mêmes sont des % — un écart de taux n'est pas
  // lui-même un taux (ex: "+4 points de réussite", jamais "+4%").
  const formaterValeur = (v: number) => (unite === "%" ? formaterPourcentage(v, 1) : formaterDecimale(v, 1));
  return (
    <div className="rounded-2xl border border-[color:var(--color-positif-pale)] bg-white p-[18px_20px]">
      <div className="text-[13px] font-bold text-texte">{titre}</div>
      <div className={`mt-1.5 font-ui text-[34px] font-extrabold leading-none ${positif ? "text-positif" : "text-attention"}`}>
        {positif ? "+" : ""}
        {formaterDecimale(ecart, 1)} pts
      </div>
      {/* Comparatif en dessous du chiffre vedette, même position que sur les
          cartes de stats du brevet — le mettre à côté (essayé d'abord)
          rendait le texte trop long et mal positionné. */}
      <div className="mt-3 flex gap-1.5 border-t border-[color:var(--color-positif-pale)] pt-2.5 text-[12px] font-semibold text-texte-doux">
        <span>attendu {formaterValeur(attendu)}</span>
        <span>→</span>
        <span>
          obtenu <b className="text-texte">{formaterValeur(obtenu)}</b>
        </span>
      </div>
    </div>
  );
}

export function ValeurAjoutee({ valeurAjoutee }: { valeurAjoutee: ValeurAjouteeDetail | null }) {
  return (
    <div className="mt-4 scroll-mt-28">
      <div className="font-titre text-[25px] font-semibold text-texte">La valeur ajoutée</div>
      <p className="mt-1 max-w-[660px] text-[12.5px] leading-relaxed text-texte-doux">
        L&apos;écart entre le résultat obtenu et celui qu&apos;obtiennent en moyenne des collèges au profil
        d&apos;élèves comparable.
      </p>

      {valeurAjoutee ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {valeurAjoutee.taux_attendu != null && valeurAjoutee.taux_observe != null && (
            <CarteVa
              titre="Réussite au brevet"
              attendu={valeurAjoutee.taux_attendu}
              obtenu={valeurAjoutee.taux_observe}
              unite="%"
            />
          )}
          {valeurAjoutee.note_attendue != null && valeurAjoutee.note_observee != null && (
            <CarteVa
              titre="Note à l'écrit"
              attendu={valeurAjoutee.note_attendue}
              obtenu={valeurAjoutee.note_observee}
              unite="pts"
            />
          )}
        </div>
      ) : (
        <p className="mt-4 text-[12.5px] text-texte-doux">
          La valeur ajoutée n&apos;est pas calculée pour cet établissement : généralement parce que l&apos;effectif
          de candidats est insuffisant (moins de 40) pour produire une estimation fiable.
        </p>
      )}
    </div>
  );
}
