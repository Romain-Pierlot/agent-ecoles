import type { ValeurAjouteeDetail } from "@/lib/types";

function CarteVa({ titre, attendu, obtenu, unite }: { titre: string; attendu: number; obtenu: number; unite: string }) {
  const ecart = obtenu - attendu;
  const positif = ecart >= 0;
  const suffixe = unite === "%" ? "%" : "";
  return (
    <div className="rounded-2xl border border-[color:var(--color-positif-pale)] bg-white p-[18px_20px]">
      <div className="text-[13px] font-bold text-texte">{titre}</div>
      <div className={`mt-1.5 font-baloo text-[34px] font-extrabold leading-none ${positif ? "text-positif" : "text-attention"}`}>
        {positif ? "+" : ""}
        {ecart.toFixed(1)}
        {unite === "pts" ? " pts" : ""}
      </div>
      {/* Comparatif en dessous du chiffre vedette, même position que sur les
          cartes de stats du brevet — le mettre à côté (essayé d'abord)
          rendait le texte trop long et mal positionné. */}
      <div className="mt-3 flex gap-1.5 border-t border-[color:var(--color-positif-pale)] pt-2.5 text-[12px] font-semibold text-texte-doux">
        <span>
          attendu {attendu.toFixed(1)}
          {suffixe}
        </span>
        <span>→</span>
        <span>
          obtenu <b className="text-texte">{obtenu.toFixed(1)}{suffixe}</b>
        </span>
      </div>
    </div>
  );
}

export function ValeurAjoutee({ valeurAjoutee }: { valeurAjoutee: ValeurAjouteeDetail | null }) {
  return (
    <div className="mt-4 rounded-[22px] border-2 border-[color:var(--color-positif-pale)] bg-fond-carte p-6">
      <div className="font-baloo text-[25px] font-extrabold text-texte">La valeur ajoutée</div>
      <p className="mt-1 max-w-[660px] text-[12.5px] leading-relaxed text-texte-doux">
        On compare les résultats obtenus à ceux attendus compte tenu du profil des élèves. Un écart positif = le
        collège fait progresser ses élèves au-delà des prévisions.
      </p>

      {valeurAjoutee ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {valeurAjoutee.taux_attendu != null && valeurAjoutee.taux_observe != null && (
            <CarteVa
              titre="Réussite au brevet vs attendu"
              attendu={valeurAjoutee.taux_attendu}
              obtenu={valeurAjoutee.taux_observe}
              unite="%"
            />
          )}
          {valeurAjoutee.note_attendue != null && valeurAjoutee.note_observee != null && (
            <CarteVa
              titre="Note à l'écrit vs attendu"
              attendu={valeurAjoutee.note_attendue}
              obtenu={valeurAjoutee.note_observee}
              unite="pts"
            />
          )}
        </div>
      ) : (
        <p className="mt-4 text-[12.5px] text-texte-doux">
          La valeur ajoutée n&apos;est pas calculée pour cet établissement — généralement parce que l&apos;effectif
          de candidats est insuffisant (moins de 40) pour produire une estimation fiable.
        </p>
      )}
    </div>
  );
}
