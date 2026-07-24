import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";

export function TopBar() {
  return (
    <div className="sticky top-0 z-40 h-16 flex-none border-b border-filet bg-fond-creme">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between px-4 md:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="h-[27px] w-[27px] -rotate-6 rounded-[9px_7px_10px_6px] bg-action" />
          <span className="font-baloo text-[21px] font-extrabold text-texte">écoles</span>
        </Link>
        <div className="flex items-center gap-5.5">
          <div className="hidden items-center gap-5.5 text-[13px] font-semibold text-texte-doux md:flex">
            <Link href="/recherche" className="hover:text-texte">Rechercher</Link>
            <Link href="/mon-secteur" className="hover:text-texte">Carte scolaire</Link>
            <Link href="/explorer" className="hover:text-texte">Explorer</Link>
            <Link href="/comprendre/ips" className="hover:text-texte">Comprendre</Link>
          </div>
          <Link
            href="/assistant"
            className="rounded-[18px] bg-action px-[15px] py-2 text-[12.5px] font-bold text-white"
          >
            Demander à {NOM_ASSISTANT}
          </Link>
        </div>
      </div>
    </div>
  );
}
