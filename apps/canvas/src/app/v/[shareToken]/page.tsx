import { createClient } from "@/lib/supabase/server";
import ViewDashboard from "./view-dashboard";

interface ViewPageProps {
  params: Promise<{ shareToken: string }>;
  searchParams: Promise<{ edit?: string }>;
}

export default async function ViewPage({ params, searchParams }: ViewPageProps) {
  const { shareToken } = await params;
  const { edit } = await searchParams;
  const isEditMode = edit === "true";

  // Get current user for permission-gated edit button
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const userId = user?.id ?? null;
  const isAdmin = (user?.app_metadata?.role as string) === "admin";

  return (
    <ViewDashboard
      shareToken={shareToken}
      initialEditMode={isEditMode}
      userId={userId}
      isAdmin={isAdmin}
    />
  );
}
