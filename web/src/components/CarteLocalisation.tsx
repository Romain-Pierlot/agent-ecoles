"use client";

import dynamic from "next/dynamic";

// Chargement client-only obligatoire : react-leaflet a besoin de `window` au
// rendu, incompatible avec le rendu serveur (cf. doc Next locale, ssr:false
// interdit dans un composant serveur — ce wrapper client existe pour ça).
const CarteLocalisationCarte = dynamic(() => import("./CarteLocalisationCarte"), {
  ssr: false,
});

export function CarteLocalisation({
  latitude,
  longitude,
  nom,
}: {
  latitude: number;
  longitude: number;
  nom: string;
}) {
  return <CarteLocalisationCarte latitude={latitude} longitude={longitude} nom={nom} />;
}
