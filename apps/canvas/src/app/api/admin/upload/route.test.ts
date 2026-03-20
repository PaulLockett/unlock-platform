import { describe, it, expect, vi, beforeEach } from "vitest";
import { expectJson } from "@/__tests__/helpers";

const mocks = vi.hoisted(() => {
  class MockAuthError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.name = "AuthError";
      this.status = status;
    }
  }
  const mockGetSessionUser = vi.fn();
  const mockRequireAuth = vi.fn();
  const mockRequireAdmin = vi.fn();
  const mockExecute = vi.fn().mockResolvedValue({ success: true });
  const mockGetTemporalClient = vi.fn().mockResolvedValue({
    workflow: { execute: mockExecute },
  });
  const mockUser = { id: "user-123", email: "testuser@example.com", role: "user" };
  const mockAdmin = { id: "admin-456", email: "admin@example.com", role: "admin" };
  const mockUpload = vi.fn().mockResolvedValue({ error: null });
  const mockGetPublicUrl = vi.fn().mockReturnValue({
    data: { publicUrl: "https://storage.example.com/test.csv" },
  });
  const mockCreateClient = vi.fn().mockResolvedValue({
    storage: {
      from: vi.fn().mockReturnValue({
        upload: mockUpload,
        getPublicUrl: mockGetPublicUrl,
      }),
    },
  });
  return {
    MockAuthError, mockGetSessionUser, mockRequireAuth, mockRequireAdmin,
    mockExecute, mockGetTemporalClient, mockUser, mockAdmin,
    mockUpload, mockGetPublicUrl, mockCreateClient,
  };
});

vi.mock("@/lib/auth/session", () => ({
  getSessionUser: mocks.mockGetSessionUser,
  requireAuth: mocks.mockRequireAuth,
  requireAdmin: mocks.mockRequireAdmin,
  AuthError: mocks.MockAuthError,
}));
vi.mock("@/lib/temporal/client", () => ({
  getTemporalClient: mocks.mockGetTemporalClient,
  TASK_QUEUES: { DATA_MANAGER: "data-manager-queue", CONFIG_ACCESS: "config-access-queue" },
}));
vi.mock("@/lib/supabase/server", () => ({
  createClient: mocks.mockCreateClient,
}));

import { NextRequest } from "next/server";
import { POST } from "./route";

function createTestFile(name: string, content: string, type: string): File {
  return new File([content], name, { type });
}

function buildUploadRequest(file: File, sourceName: string): NextRequest {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("source_name", sourceName);
  return new NextRequest(new URL("http://localhost:3000/api/admin/upload"), {
    method: "POST",
    body: formData,
  });
}

describe("POST /api/admin/upload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({ success: true, records_ingested: 10 });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
    mocks.mockUpload.mockResolvedValue({ error: null });
    mocks.mockCreateClient.mockResolvedValue({
      storage: {
        from: vi.fn().mockReturnValue({
          upload: mocks.mockUpload,
          getPublicUrl: mocks.mockGetPublicUrl,
        }),
      },
    });
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Not authenticated", 401));
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const req = buildUploadRequest(file, "test-source");
    const res = await POST(req);
    const json = await expectJson(res, 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 403 when not admin", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Admin access required", 403));
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const req = buildUploadRequest(file, "test-source");
    const res = await POST(req);
    const json = await expectJson(res, 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Admin access required");
  });

  it("returns 400 when file is missing", async () => {
    const formData = new FormData();
    formData.append("source_name", "test-source");
    const req = new NextRequest(new URL("http://localhost:3000/api/admin/upload"), {
      method: "POST",
      body: formData,
    });
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
    expect(json.message).toBe("file and source_name are required");
  });

  it("returns 400 when source_name is missing", async () => {
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const formData = new FormData();
    formData.append("file", file);
    const req = new NextRequest(new URL("http://localhost:3000/api/admin/upload"), {
      method: "POST",
      body: formData,
    });
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
    expect(json.message).toBe("file and source_name are required");
  });

  it("returns 400 on invalid file type", async () => {
    const file = createTestFile("malware.exe", "bad content", "application/octet-stream");
    const req = buildUploadRequest(file, "test-source");
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Only CSV and JSON files are supported");
  });

  it("returns 400 on file too large", async () => {
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const req = buildUploadRequest(file, "test-source");
    // Mock formData to return a file with overridden size
    const mockFile = {
      name: "data.csv",
      type: "text/csv",
      size: 51 * 1024 * 1024,
      arrayBuffer: () => file.arrayBuffer(),
    };
    const mockFormData = new Map<string, unknown>([
      ["file", mockFile],
      ["source_name", "test-source"],
      ["resource_type", null],
      ["channel_key", null],
    ]);
    vi.spyOn(req, "formData").mockResolvedValue({
      get: (key: string) => mockFormData.get(key) ?? null,
    } as unknown as FormData);
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
    expect(json.message).toBe("File must be under 50MB");
  });

  it("returns 500 when Supabase upload fails", async () => {
    mocks.mockUpload.mockResolvedValue({ error: { message: "Storage quota exceeded" } });
    mocks.mockCreateClient.mockResolvedValue({
      storage: {
        from: vi.fn().mockReturnValue({
          upload: mocks.mockUpload,
          getPublicUrl: mocks.mockGetPublicUrl,
        }),
      },
    });
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const req = buildUploadRequest(file, "test-source");
    const res = await POST(req);
    const json = await expectJson(res, 500);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Upload failed: Storage quota exceeded");
  });

  it("executes IngestWorkflow after upload", async () => {
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const req = buildUploadRequest(file, "test-source");
    await POST(req);
    expect(mocks.mockExecute).toHaveBeenCalledWith("IngestWorkflow", {
      taskQueue: "data-manager-queue",
      workflowId: expect.stringMatching(/^upload-ingest-test-source-\d+$/),
      args: [
        expect.objectContaining({
          source_name: "test-source",
          source_type: "file_csv",
          resource_type: "posts",
          base_url: "https://storage.example.com/test.csv",
          max_pages: 1,
        }),
      ],
    });
  });

  it("returns success with file_url", async () => {
    const file = createTestFile("data.csv", "a,b\n1,2", "text/csv");
    const req = buildUploadRequest(file, "test-source");
    const res = await POST(req);
    const json = await expectJson(res, 200);
    expect(json.success).toBe(true);
    expect(json.file_url).toBe("https://storage.example.com/test.csv");
    expect(json.message).toBe("File uploaded and ingestion started");
  });
});
