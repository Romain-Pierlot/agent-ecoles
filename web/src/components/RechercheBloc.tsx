// Bloc de recherche ville/adresse — présent sur les pages hub (région,
// département) et la page terminale ville (cf. docs/Design_system/
// hub_departement_comparateur/README.md). Extrait de ZoneHub pour éviter
// une 3ᵉ copie identique sur la page ville.
export function RechercheBloc({
  placeholder = "Rechercher une ville ou une adresse…",
}: {
  placeholder?: string;
}) {
  return (
    <form
      action="/recherche"
      method="get"
      className="mt-6 flex flex-wrap items-center gap-2.5 rounded-2xl border border-filet bg-white p-4"
    >
      <input
        type="text"
        name="q"
        placeholder={placeholder}
        className="min-w-[240px] flex-1 rounded-xl border border-filet-fonce bg-fond-carte px-3.5 py-2.5 text-[13.5px] text-texte outline-none placeholder:text-texte-doux/60"
      />
      <button
        type="submit"
        className="rounded-xl bg-action px-5 py-2.5 text-[13px] font-bold text-white hover:bg-action-dark"
      >
        Rechercher
      </button>
    </form>
  );
}
