import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{
    regionSlug: string;
    deptSlug: string;
    villeSlug: string;
    collegeSlug: string;
  }>;
}) {
  const { regionSlug, deptSlug, villeSlug, collegeSlug } = await params;
  return (
    <PagePlaceholder
      titre="Fiche établissement"
      chemin="/region/[regionSlug]/departement/[deptSlug]/ville/[villeSlug]/college/[collegeSlug]"
      params={{ regionSlug, deptSlug, villeSlug, collegeSlug }}
    />
  );
}
