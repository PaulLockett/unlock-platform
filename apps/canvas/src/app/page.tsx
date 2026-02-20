import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import SignOutButton from "./sign-out-button";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-col items-center gap-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-black dark:text-zinc-50">
          Unlock Alabama Data Platform
        </h1>
        <p className="max-w-md text-lg text-zinc-600 dark:text-zinc-400">
          Analytics Canvas — civic data transformation and insights
        </p>
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Signed in as <strong>{user.email}</strong>
          </p>
          <SignOutButton />
        </div>
      </main>
    </div>
  );
}
