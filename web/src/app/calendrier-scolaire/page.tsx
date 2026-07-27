import Link from "next/link";
import { recupererCalendrierScolaire } from "@/lib/calendrierScolaire";
import { TableauMetropole } from "./_components/TableauMetropole";
import { CartesMetropoleMobile } from "./_components/CartesMetropoleMobile";
import { TableauOutreMer } from "./_components/TableauOutreMer";

export const metadata = {
  title: "Calendrier scolaire : vacances par zone | agent-ecoles",
  description: "Dates des vacances scolaires par zone (A, B, C, Corse) et par territoire d'outre-mer.",
};

export default async function Page() {
  const calendrier = await recupererCalendrierScolaire();
  const anneeScolaire = calendrier.metropole[0]?.annee_scolaire ?? "";

  return (
    <div className="min-h-screen bg-fond-creme text-texte">
      <div className="mx-auto w-full max-w-[1280px] px-4.5 pb-16 pt-4.5 md:px-11">
        {/* ===== FIL D'ARIANE ===== */}
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <Link href="/comprendre" className="hover:text-texte-doux">Comprendre</Link>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">Calendrier scolaire</span>
        </div>

        <h1 className="font-titre text-[29px] font-semibold leading-[1.08] text-texte md:text-[44px] md:leading-[1.06]">
          Vacances scolaires {anneeScolaire}
        </h1>
        <h2 className="mt-2.5 font-titre text-[21px] font-semibold text-texte md:text-[26px]">Métropole</h2>

        <div className="mt-4">
          <TableauMetropole metropole={calendrier.metropole} academies={calendrier.academies} />
          <CartesMetropoleMobile metropole={calendrier.metropole} academies={calendrier.academies} />
        </div>

        <p className="mt-3.5 max-w-[1000px] font-ui text-[13px] leading-[1.6] text-texte-doux">
          Les vacances débutent les jours indiqués, après les cours. Pour les élèves qui n&apos;ont pas
          cours le samedi, les vacances débutent le vendredi après les cours. Les cours reprennent le
          matin des jours indiqués.
        </p>

        <div className="mt-3.5 flex items-start gap-3.5 rounded-[14px] border border-filet-fonce bg-fond-encart px-5 py-4">
          <span className="flex-none rounded-[7px] bg-texte px-[11px] py-1 font-ui text-[11px] font-extrabold tracking-[.04em] text-fond-sable">
            À noter
          </span>
          <div>
            <p className="font-ui text-[13.5px] font-medium text-texte">
              Dans les zones A, B et C, les élèves n&apos;auront pas classe le vendredi 7 mai 2027.
            </p>
            <p className="mt-[5px] font-ui text-[12.5px] text-texte-doux">
              En Corse : classes vaquées le mardi 8 septembre 2026 et le vendredi 7 mai 2027, journée
              banalisée le mardi 8 décembre 2026, lundi de Pentecôte (17 mai 2027) sans école.
            </p>
          </div>
        </div>

        <a
          href="#outre-mer"
          className="mt-6 block rounded-2xl bg-fond-sable px-5 py-4 font-ui text-[13.5px] font-bold text-texte hover:underline md:hidden"
        >
          Voir aussi les dates outre-mer ↓
        </a>
      </div>

      <TableauOutreMer outreMer={calendrier.outre_mer} />

      <div className="mx-auto w-full max-w-[1280px] px-4.5 py-9 md:px-11">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-[14px] border border-filet-fonce bg-fond-encart px-5.5 py-4.5">
          <div>
            <p className="font-ui text-[13px] font-bold text-texte">D&apos;où viennent ces dates</p>
            <p className="mt-1 max-w-[640px] font-ui text-[12.5px] leading-[1.6] text-texte-doux">
              Zones A/B/C : arrêté du 22 octobre 2025 (JORF n°0250 du 23 octobre 2025, texte n°15).
              Corse : académie de Corse. Outre-mer : calendriers publiés par le ministère de l&apos;Éducation
              nationale.
            </p>
          </div>
          <a
            href="https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052416058"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto font-ui text-[13px] font-bold text-action underline decoration-2 underline-offset-[3px] hover:text-action-dark"
          >
            Consulter l&apos;arrêté →
          </a>
        </div>
      </div>
    </div>
  );
}
