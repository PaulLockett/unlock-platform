import { vi } from "vitest";

// Silence console.error during tests to keep output clean
vi.spyOn(console, "error").mockImplementation(() => {});

// Set placeholder env vars that routes check at runtime
process.env.LIVEBLOCKS_SECRET_KEY = "sk-test-liveblocks-key";
process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:54321";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "test-anon-key";
