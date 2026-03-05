import ViewDashboard from "./view-dashboard";

interface ViewPageProps {
  params: Promise<{ shareToken: string }>;
  searchParams: Promise<{ edit?: string }>;
}

export default async function ViewPage({ params, searchParams }: ViewPageProps) {
  const { shareToken } = await params;
  const { edit } = await searchParams;
  const isEditMode = edit === "true";

  return <ViewDashboard shareToken={shareToken} initialEditMode={isEditMode} />;
}
