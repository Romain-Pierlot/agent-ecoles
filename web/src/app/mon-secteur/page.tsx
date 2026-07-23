import Link from "next/link";
import { recupererSecteur } from "@/lib/secteur";
import { NOM_ASSISTANT } from "@/lib/constants";
import { AgentBlock } from "@/components/AgentBlock";
import { ChampAdresse } from "./_components/ChampAdresse";
import { BlocTrouve } from "./_components/BlocTrouve";
import { BlocMultiSecteur } from "./_components/BlocMultiSecteur";
import { BlocNonDeterminable } from "./_components/BlocNonDeterminable";
import { BlocAdresseNonReconnue } from "./_components/BlocAdresseNonReconnue";
import { BlocAdresseAmbigue } from "./_components/BlocAdresseAmbigue";

// Next.js fournit un tableau si un paramètre est répété dans l'URL — même
// garde que /recherche/page.tsx.
function premiereValeur(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

// Titre/sous-titre du bloc Camille contextuels par état (cf. maquette) —
// "trouve" et "adresse_non_reconnue" partagent le même message par défaut
// (la maquette de référence ne prévoit pas de texte dédié à une adresse non
// reconnue, elle retombe sur ce même cas par défaut).
function camilleContextuel(etat: string | undefined) {
  if (etat === "multi_secteur") {
    // Générique plutôt que "Deux collèges..." : le nombre réel de
    // candidats varie (cas réel à 3, cf. Maxéville/Rue Blaise Pascal),
    // contrairement à l'exemple à 2 de la maquette.
    return {
      titre: "Plusieurs collèges possibles — lequel choisir ?",
      sousTitre: `${NOM_ASSISTANT} compare les chiffres pour votre situation.`,
    };
  }
  if (etat === "non_determinable") {
    return {
      titre: "Pas sûr de votre rattachement ?",
      sousTitre: `${NOM_ASSISTANT} peut vous aider à comprendre la carte scolaire et vos options.`,
    };
  }
  if (etat === "adresse_ambigue") {
    return {
      titre: "Pas sûr de votre adresse exacte ?",
      sousTitre: `${NOM_ASSISTANT} peut vous aider à préciser votre situation.`,
    };
  }
  return {
    titre: "Votre secteur, mais aussi le privé et les dérogations",
    sousTitre: `${NOM_ASSISTANT} vous explique vos options au-delà du collège de rattachement.`,
  };
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const tousParams = await searchParams;
  const adresse = (premiereValeur(tousParams.adresse) ?? "").trim();

  const resultats = adresse ? await recupererSecteur(adresse) : null;
  const camille = camilleContextuel(resultats?.etat);
  const afficherBandeauAdresse =
    resultats && (resultats.etat === "trouve" || resultats.etat === "multi_secteur" || resultats.etat === "non_determinable");

  return (
    <div className="min-h-full flex-1 bg-fond-creme">
      <div className="mx-auto max-w-2xl px-4 pb-1.5 pt-8 text-center md:px-8">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-[#CDE3D4] bg-[#EEF4EF] px-3.5 py-1 text-[11px] font-bold uppercase tracking-[0.06em] text-[#227049]">
          Carte scolaire officielle du Ministère
        </span>
        <h1 className="mt-3.5 font-baloo text-[31px] font-extrabold leading-tight text-texte">
          Quel est mon collège de secteur ?
        </h1>
        <p className="mx-auto mt-2 max-w-md text-[14.5px] leading-relaxed text-texte-doux">
          Saisissez votre adresse pour connaître votre{" "}
          <b className="text-texte">collège de rattachement administratif</b>, celui de la carte scolaire, ainsi que
          les collèges situés autour de chez vous.
        </p>

        {/* key=adresse force un remontage à chaque navigation (clic sur une
            suggestion d'adresse ambiguë, "Modifier"...) — sans ça,
            useState(adresseInitiale) ne se réexécute qu'au premier montage
            et le champ garde l'ancien texte tapé après la résolution. */}
        <ChampAdresse key={adresse} adresseInitiale={adresse} />
        <p className="mx-auto mt-2.5 max-w-md text-[12px] leading-relaxed text-[#A8987F]">
          Le rattachement dépend de l&apos;adresse exacte. Il n&apos;est pas toujours déterminable au numéro près
          dans les données officielles — dans ce cas nous vous l&apos;indiquons clairement.
        </p>
      </div>

      <div className="mx-auto max-w-2xl px-4 pb-16 pt-4 md:px-8">
        {resultats && (
          <>
            {afficherBandeauAdresse && (
              <div className="mb-3.5 flex items-center gap-2.5 rounded-[13px] border-[1.5px] border-filet bg-white p-3">
                <span className="text-[15px]">📍</span>
                <div className="min-w-0 flex-1">
                  <span className="text-[13px] font-bold text-texte">{resultats.adresse_normalisee ?? adresse}</span>
                  <span className="text-[12px] text-texte-doux"> — adresse géolocalisée</span>
                </div>
                <Link href="/mon-secteur" className="text-[12px] font-bold text-action-dark hover:text-action">
                  Modifier
                </Link>
              </div>
            )}

            {resultats.etat === "trouve" && <BlocTrouve resultats={resultats} />}
            {resultats.etat === "multi_secteur" && <BlocMultiSecteur resultats={resultats} />}
            {resultats.etat === "non_determinable" && <BlocNonDeterminable resultats={resultats} />}
            {resultats.etat === "adresse_ambigue" && (
              <BlocAdresseAmbigue suggestions={resultats.suggestions_ambigues} />
            )}
            {resultats.etat === "adresse_non_reconnue" && <BlocAdresseNonReconnue adresse={adresse} />}
          </>
        )}

        <AgentBlock
          exemple={`Quels collèges autour de ${resultats?.colleges_secteur[0]?.commune ?? "chez moi"} correspondent à mes critères ?`}
          titre={camille.titre}
          sousTitre={camille.sousTitre}
        />
      </div>

      <div className="border-t border-filet bg-fond-sable">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4.5 text-[12px] font-semibold text-texte-doux md:px-8">
          <span>Rattachement d&apos;après la carte scolaire officielle du Ministère · à confirmer auprès de votre rectorat</span>
          <span className="flex gap-4.5">
            <Link href="/methodologie" className="hover:text-texte">Notre méthode</Link>
            <Link href="/sources" className="hover:text-texte">Sources</Link>
            <Link href="/a-propos" className="hover:text-texte">À propos</Link>
          </span>
        </div>
      </div>
    </div>
  );
}
