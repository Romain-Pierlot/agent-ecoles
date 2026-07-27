import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  // /methodologie a déménagé sous /comprendre/methodologie (le fil
  // d'Ariane des notes de méthode y affiche "Comprendre › Méthodologie du
  // site › ..."). Redirection permanente au cas où l'ancienne URL a déjà
  // été indexée.
  async redirects() {
    return [
      {
        source: "/methodologie",
        destination: "/comprendre/methodologie",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
