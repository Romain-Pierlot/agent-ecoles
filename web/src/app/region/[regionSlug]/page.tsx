import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ regionSlug: string }>;
}) {
  const { regionSlug } = await params;
  return <PagePlaceholder titre="Région" chemin="/region/[regionSlug]" params={{ regionSlug }} />;
}
