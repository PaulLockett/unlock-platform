import { redirect } from "next/navigation";
import { getSessionUser } from "@/lib/auth/session";

/**
 * Admin layout guard — redirects non-admin users to the home page.
 */
export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getSessionUser();

  if (!user) {
    redirect("/login");
  }

  if (user.role !== "admin") {
    redirect("/");
  }

  return <>{children}</>;
}
