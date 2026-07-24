"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapContainer, Marker, TileLayer } from "react-leaflet";

// Pin en divIcon (SVG inline) plutôt que l'icône par défaut de Leaflet : évite
// le bug classique des icônes cassées par les bundlers modernes (chemins
// d'images résolus à l'exécution que webpack/turbopack ne retrouvent pas), et
// permet d'utiliser la couleur --color-action de la charte plutôt que le bleu
// générique de Leaflet.
const ICONE_PIN = L.divIcon({
  className: "",
  html: `<svg width="30" height="42" viewBox="0 0 30 42" xmlns="http://www.w3.org/2000/svg">
    <path d="M15 0C6.7 0 0 6.7 0 15c0 11.25 15 27 15 27s15-15.75 15-27C30 6.7 23.3 0 15 0z" fill="#D9457A" stroke="#A82C58" stroke-width="1.5"/>
    <circle cx="15" cy="15" r="6" fill="white"/>
  </svg>`,
  iconSize: [24, 34],
  iconAnchor: [12, 34],
});

// Échelle "quartier" : suffisant pour situer l'établissement sans viser une
// précision parcelle par parcelle, cf. conception validée.
const ZOOM_QUARTIER = 10;

export default function CarteLocalisationCarte({
  latitude,
  longitude,
  nom,
}: {
  latitude: number;
  longitude: number;
  nom: string;
}) {
  return (
    <div>
      <div
        role="img"
        aria-label={`Carte de localisation : ${nom}`}
        className="h-[180px] overflow-hidden rounded-[22px_18px_22px_20px] border-2 border-filet"
      >
        {/* Tous les gestes désactivés : cette carte sert à situer
            l'établissement d'un coup d'œil, pas à naviguer dedans (cf.
            conception validée, conflit de geste scroll/pan sur mobile). */}
        <MapContainer
          center={[latitude, longitude]}
          zoom={ZOOM_QUARTIER}
          dragging={false}
          scrollWheelZoom={false}
          touchZoom={false}
          doubleClickZoom={false}
          boxZoom={false}
          keyboard={false}
          zoomControl={false}
          style={{ height: "100%", width: "100%" }}
        >
          {/* Test CARTO Positron plutôt que le rendu OSM Standard : moins
              chargé visuellement, et tuiles retina ({r} -> @2x sur écran
              haute densité) via detectRetina, sans clé API. */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            subdomains="abcd"
            detectRetina
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          <Marker position={[latitude, longitude]} icon={ICONE_PIN} />
        </MapContainer>
      </div>
      <a
        href={`https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=${ZOOM_QUARTIER}/${latitude}/${longitude}`}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-1.5 block text-center text-[11px] font-semibold text-action-dark underline underline-offset-2"
      >
        Voir en grand sur OpenStreetMap
      </a>
    </div>
  );
}
