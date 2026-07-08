import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ villeSlug: string }>;
}) {
  const { villeSlug } = await params;
  return <PagePlaceholder titre="Ville / commune" chemin="/ville/[villeSlug]" params={{ villeSlug }} />;
}
