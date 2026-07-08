import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ academieSlug: string }>;
}) {
  const { academieSlug } = await params;
  return (
    <PagePlaceholder
      titre="Académie (rattachement transverse)"
      chemin="/academie/[academieSlug]"
      params={{ academieSlug }}
    />
  );
}
