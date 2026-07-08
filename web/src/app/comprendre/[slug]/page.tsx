import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <PagePlaceholder titre="Guide — Comprendre" chemin="/comprendre/[slug]" params={{ slug }} />
  );
}
