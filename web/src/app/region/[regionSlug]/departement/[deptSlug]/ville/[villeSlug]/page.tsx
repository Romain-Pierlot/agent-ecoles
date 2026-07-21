import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ regionSlug: string; deptSlug: string; villeSlug: string }>;
}) {
  const { regionSlug, deptSlug, villeSlug } = await params;
  return (
    <PagePlaceholder
      titre="Ville / commune"
      chemin="/region/[regionSlug]/departement/[deptSlug]/ville/[villeSlug]"
      params={{ regionSlug, deptSlug, villeSlug }}
    />
  );
}
