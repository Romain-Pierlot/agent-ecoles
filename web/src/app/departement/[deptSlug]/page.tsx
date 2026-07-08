import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ deptSlug: string }>;
}) {
  const { deptSlug } = await params;
  return (
    <PagePlaceholder titre="Département" chemin="/departement/[deptSlug]" params={{ deptSlug }} />
  );
}
