import Image from "next/image";
import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";

const VILLES_POPULAIRES = ["Paris", "Lyon", "Marseille", "Rhône (69)", "Toulouse"];

const CARTES_COMPRENDRE = [
  {
    slug: "ips",
    titre: "L'IPS, c'est quoi ?",
    texte: "Le profil social des élèves, en une phrase — une lecture, pas une note.",
    fondClass: "bg-descriptif-pale",
    texteClass: "text-descriptif",
  },
  {
    slug: "valeur-ajoutee",
    titre: "La valeur ajoutée",
    texte: "Ce que le collège apporte vraiment à ses élèves.",
    fondClass: "bg-positif-pale",
    texteClass: "text-positif",
  },
  {
    slug: "carte-scolaire",
    titre: "La carte scolaire",
    texte: "Quel collège correspond à votre adresse.",
    fondClass: "bg-action-pale",
    texteClass: "text-action-dark",
  },
];

export default function Page() {
  return (
    <div className="bg-fond-creme text-texte font-figtree min-h-screen">
      {/* ===== HERO ===== */}
      <div className="mx-auto max-w-6xl px-4 md:px-8 pb-5 pt-8">
        <div className="mx-auto mb-9 max-w-xl text-center">
          <span className="inline-block -rotate-1 rounded-2xl border border-dashed border-[#EDA9C2] bg-action-pale px-4 py-1.5 text-xs font-bold text-action-dark">
            Pensé par des parents, pas par un algorithme
          </span>
          <h1 className="mt-4 font-baloo text-[clamp(38px,5vw,54px)] font-extrabold leading-[1.05] text-texte">
            Choisir un collège,
            <br />
            on y voit{" "}
            <span className="text-action underline decoration-wavy decoration-[#F0C8D8] decoration-4 underline-offset-[10px]">
              clair ensemble.
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-md text-[16.5px] leading-relaxed text-texte-doux">
            Racontez votre situation à {NOM_ASSISTANT}{" "}
            comme à une amie qui s&apos;y connaît. Elle traduit les chiffres officiels en repères
            simples — vous gardez la décision.
          </p>
        </div>

        <div className="mx-auto grid max-w-4xl items-stretch gap-7 md:grid-cols-[1.4fr_0.8fr]">
          {/* CHAT WINDOW */}
          <div className="flex flex-col overflow-hidden rounded-[28px_22px_28px_24px] border-2 border-filet bg-white shadow-[0_18px_44px_rgba(34,59,48,0.13)]">
            <div className="flex items-center gap-3 border-b border-[#F1EADA] bg-[#FDEFF4] px-5 py-4">
              <div className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action font-baloo text-lg font-extrabold text-white">
                {NOM_ASSISTANT.charAt(0)}
              </div>
              <div className="flex-1">
                <div className="font-baloo text-[15px] font-bold text-texte">
                  {NOM_ASSISTANT} · votre guide
                </div>
                <div className="text-[11.5px] font-semibold text-positif">
                  ● là pour vous aider
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3 p-5">
              <div className="max-w-[74%] self-end rounded-[16px_16px_5px_16px] bg-action-pale px-[15px] py-3 text-[13.5px] leading-relaxed text-[#8A2350]">
                Ma fille entre en 6ᵉ à Lyon 5ᵉ. J&apos;aimerais un collège avec une chorale, et pas
                trop loin.
              </div>
              <div className="max-w-[92%] self-start">
                <div className="rounded-[16px_16px_16px_5px] border border-[#F1E7D3] bg-fond-carte px-4 py-3.5 text-[13.5px] leading-relaxed text-texte">
                  Bien sûr ! Deux collèges publics à moins d&apos;1 km avec une chorale, qui font{" "}
                  <b>progresser</b>
                  {" "}leurs élèves au-delà de ce qu&apos;on attendrait :
                  <div className="mt-3 flex flex-col gap-2">
                    <div className="rounded-[15px_13px_16px_12px] border border-filet bg-white p-3 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-baloo text-sm font-bold text-texte">
                          Collège Jean Moulin
                        </span>
                        <span className="rounded-xl bg-positif-pale px-2.5 py-0.5 text-[10.5px] font-bold text-positif">
                          +6 valeur ajoutée
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {["Chorale", "0,8 km", "ULIS"].map((tag) => (
                          <span
                            key={tag}
                            className="rounded-xl bg-fond-sable px-2.5 py-0.5 text-[10.5px] font-semibold text-[#6B6250]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-[14px_16px_12px_15px] border border-filet bg-white p-3 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-baloo text-sm font-bold text-texte">
                          Collège des Battières
                        </span>
                        <span className="rounded-xl bg-positif-pale px-2.5 py-0.5 text-[10.5px] font-bold text-positif">
                          +2 valeur ajoutée
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {["Chorale", "1,2 km"].map((tag) => (
                          <span
                            key={tag}
                            className="rounded-xl bg-fond-sable px-2.5 py-0.5 text-[10.5px] font-semibold text-[#6B6250]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  <span className="rounded-2xl border border-action bg-action px-3.5 py-1.5 text-xs font-bold text-white">
                    Comparer les deux
                  </span>
                  <span className="rounded-2xl border border-filet bg-white px-3.5 py-1.5 text-xs font-semibold text-texte-doux">
                    Et pour la cantine ?
                  </span>
                  <span className="rounded-2xl border border-filet bg-white px-3.5 py-1.5 text-xs font-semibold text-texte-doux">
                    Voir sur la carte
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-auto border-t border-[#F1EADA] px-5 pb-[18px] pt-3.5">
              <Link
                href="/assistant"
                className="flex items-center gap-2.5 rounded-2xl border border-filet-fonce bg-fond-carte py-2 pl-4 pr-2 text-[13.5px] text-[#A8987F] hover:border-action"
              >
                <span className="flex-1">Écrivez à {NOM_ASSISTANT}…</span>
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-action font-baloo text-lg font-extrabold text-white shadow-[0_4px_12px_rgba(217,69,122,0.32)]">
                  ↑
                </span>
              </Link>
            </div>
          </div>

          {/* PHOTO — version compacte sur mobile, sans éléments superposés */}
          <div className="relative h-40 w-full overflow-hidden rounded-3xl md:hidden">
            <Image
              src="https://images.unsplash.com/photo-1752652011858-302f08a6dc9f?fm=jpg&q=70&w=600&auto=format&fit=crop"
              alt="Moment parent-enfant"
              fill
              className="object-cover"
              sizes="100vw"
            />
          </div>

          {/* PHOTO COLLAGE — desktop uniquement */}
          <div className="relative hidden flex-col items-center justify-center md:flex">
            <div className="relative h-[360px] w-full overflow-hidden rounded-[46%_54%_57%_43%/53%_44%_56%_47%]">
              <Image
                src="https://images.unsplash.com/photo-1752652011858-302f08a6dc9f?fm=jpg&q=70&w=900&auto=format&fit=crop"
                alt="Moment parent-enfant"
                fill
                className="object-cover"
                sizes="(min-width: 768px) 30vw, 90vw"
              />
            </div>
            <div className="absolute left-[-12px] top-9 z-10 -rotate-3 rounded-[14px_12px_15px_11px] bg-white px-3.5 py-2.5 shadow-[0_6px_16px_rgba(34,59,48,0.14)]">
              <div className="font-baloo text-base font-extrabold text-action">9 143</div>
              <div className="text-[10px] font-semibold text-texte-doux">collèges, en clair</div>
            </div>
            <div className="absolute bottom-6 right-[-6px] z-10 h-[100px] w-[100px] overflow-hidden rounded-full border-4 border-fond-creme shadow-[0_6px_16px_rgba(34,59,48,0.16)]">
              <Image
                src="https://images.unsplash.com/photo-1527821468487-b724210d296a?fm=jpg&q=70&w=400&auto=format&fit=crop"
                alt="Enfants"
                fill
                className="object-cover"
                sizes="100px"
              />
            </div>
            <div className="absolute bottom-[-6px] left-0 rotate-[-3deg] font-caveat text-lg font-semibold text-accent">
              Plus qu&apos;un agent, un guide ✿
            </div>
          </div>
        </div>
      </div>

      {/* ===== BAND : recherche directe ===== */}
      <div className="mx-auto max-w-4xl px-4 md:px-8 pb-4 pt-8">
        <div className="flex flex-wrap items-center gap-6 rounded-[22px_18px_22px_20px] border border-filet bg-white p-6">
          <div className="flex-none">
            <div className="font-baloo text-lg font-extrabold text-texte">
              Vous savez déjà où chercher ?
            </div>
            <div className="mt-0.5 text-[13px] text-texte-doux">
              Tapez un collège, une ville, un code postal.
            </div>
          </div>
          <form
            action="/recherche"
            method="get"
            className="flex min-w-[280px] flex-1 items-center gap-2.5 rounded-2xl border border-filet-fonce bg-fond-carte py-2 pl-4 pr-2"
          >
            <span className="text-[#A8987F]">⌕</span>
            <input
              type="text"
              name="q"
              placeholder="Ex : Lyon, Jean Moulin, 69005…"
              className="flex-1 bg-transparent text-[13.5px] text-texte outline-none placeholder:text-[#A8987F]"
            />
            <button
              type="submit"
              className="cursor-pointer rounded-xl bg-action px-5 py-2.5 text-[13px] font-bold text-white hover:bg-action-dark"
            >
              Chercher
            </button>
          </form>
        </div>
        <div className="mt-3.5 flex flex-wrap items-center gap-2 pl-1">
          <span className="text-[11.5px] font-semibold text-[#8A7B64]">Souvent recherché :</span>
          {VILLES_POPULAIRES.map((ville) => (
            <Link
              key={ville}
              href={`/recherche?q=${encodeURIComponent(ville)}`}
              className="rounded-2xl border border-filet-fonce bg-white px-3.5 py-1.5 text-xs font-semibold text-texte-doux hover:border-action hover:text-action-dark"
            >
              {ville}
            </Link>
          ))}
        </div>
      </div>

      {/* ===== COMPRENDRE ===== */}
      <div className="mx-auto max-w-4xl px-4 md:px-8 pb-10 pt-6">
        <div className="mb-4 flex items-baseline gap-2.5">
          <div className="font-baloo text-[22px] font-extrabold text-texte">
            Comprendre, sans jargon
          </div>
          <div className="-rotate-2 font-caveat text-lg font-semibold text-accent">
            promis, c&apos;est simple
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {CARTES_COMPRENDRE.map((carte) => (
            <Link
              key={carte.slug}
              href={`/comprendre/${carte.slug}`}
              className={`rounded-[18px_15px_18px_14px] p-[18px] ${carte.fondClass} hover:opacity-90`}
            >
              <div className={`font-baloo mb-1.5 text-[15px] font-bold ${carte.texteClass}`}>
                {carte.titre}
              </div>
              <div className="text-[12.5px] leading-normal text-texte-doux">{carte.texte}</div>
            </Link>
          ))}
        </div>
      </div>

      {/* ===== FOOTER ===== */}
      <div className="border-t border-filet bg-fond-sable">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 md:px-8 py-[18px] text-xs font-semibold text-[#8A7B64]">
          <span>Données officielles du Ministère · mises à jour chaque année</span>
          <span className="flex gap-[18px]">
            <Link href="/methodologie" className="underline hover:text-texte">
              Notre méthode
            </Link>
            <Link href="/sources" className="underline hover:text-texte">
              Sources
            </Link>
            <Link href="/a-propos" className="underline hover:text-texte">
              À propos
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}
