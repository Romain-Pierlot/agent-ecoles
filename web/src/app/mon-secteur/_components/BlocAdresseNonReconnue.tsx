const EXEMPLES = ["12 rue des Farges, 69005 Lyon", "Villeurbanne"];

export function BlocAdresseNonReconnue({ adresse }: { adresse: string }) {
  return (
    <div className="mx-auto max-w-lg rounded-[20px] border-[1.5px] border-filet bg-white p-8.5 text-center">
      <span className="inline-flex h-12.5 w-12.5 items-center justify-center rounded-2xl bg-fond-sable font-baloo text-2xl font-extrabold text-texte-doux">
        ✕
      </span>
      <div className="mt-3.5 font-baloo text-xl font-extrabold text-texte">Adresse non reconnue</div>
      <p className="mt-2 text-[13.5px] leading-relaxed text-texte-doux">
        Nous n&apos;avons pas trouvé « {adresse} ». Vérifiez l&apos;orthographe et ajoutez la ville ou le code postal —
        par exemple <span className="font-bold text-action-dark">12 rue des Farges, 69005 Lyon</span>.
      </p>
      <div className="mt-4.5 flex flex-wrap justify-center gap-2">
        <span className="self-center text-[11.5px] font-semibold text-texte-doux">Essayez :</span>
        {EXEMPLES.map((exemple) => (
          <a
            key={exemple}
            href={`/mon-secteur?adresse=${encodeURIComponent(exemple)}`}
            className="rounded-2xl border border-filet bg-fond-carte px-3.5 py-1.5 text-[12px] font-semibold text-texte-doux hover:border-action hover:text-action-dark"
          >
            {exemple}
          </a>
        ))}
      </div>
    </div>
  );
}
