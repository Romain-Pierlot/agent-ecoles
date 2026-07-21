import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ regionSlug: string; deptSlug: string }>;
}) {
  const { regionSlug, deptSlug } = await params;
  return (
    <PagePlaceholder
      titre="Département"
      chemin="/region/[regionSlug]/departement/[deptSlug]"
      params={{ regionSlug, deptSlug }}
    />
  );
}
