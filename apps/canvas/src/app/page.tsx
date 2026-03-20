import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import DashboardClient from "./dashboard-client";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const role = (user.app_metadata?.role as string) ?? "user";
  const displayRole = role === "admin" ? "System Admin" : "Viewer";

  return (
    <DashboardClient
      userId={user.id}
      userEmail={user.email ?? ""}
      userRole={displayRole}
      isAdmin={role === "admin"}
    />
  );
}
