import { vi } from "vitest";

let _uploadError: { message: string } | null = null;
let _publicUrl = "https://storage.example.com/test-file.csv";

export function mockUploadSuccess(publicUrl?: string) {
  _uploadError = null;
  if (publicUrl) _publicUrl = publicUrl;
}

export function mockUploadError(message: string) {
  _uploadError = { message };
}

export function resetSupabaseMock() {
  _uploadError = null;
  _publicUrl = "https://storage.example.com/test-file.csv";
}

/**
 * Standard vi.mock factory for @/lib/supabase/server.
 */
export function supabaseMockFactory() {
  return {
    createClient: vi.fn().mockImplementation(async () => ({
      storage: {
        from: vi.fn().mockReturnValue({
          upload: vi.fn().mockImplementation(async () => ({
            error: _uploadError,
          })),
          getPublicUrl: vi.fn().mockReturnValue({
            data: { publicUrl: _publicUrl },
          }),
        }),
      },
    })),
  };
}
