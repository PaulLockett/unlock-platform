import { describe, it, expect, vi, beforeEach } from "vitest";
import { buildRequest, expectJson } from "@/__tests__/helpers";

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
  return {
    MockAuthError, mockGetSessionUser, mockRequireAuth, mockRequireAdmin,
    mockExecute, mockGetTemporalClient, mockUser, mockAdmin,
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

import { POST } from "./route";

describe("POST /api/configure", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({ success: true });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 400 on invalid body (missing config_type)", async () => {
    const req = buildRequest("POST", "/api/configure", { name: "test" });
    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
  });

  it("returns 400 on empty name", async () => {
    const req = buildRequest("POST", "/api/configure", {
      config_type: "view",
      name: "",
    });
    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
  });

  it("schema config_type requires admin — returns 403 for user", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(
      new mocks.MockAuthError("Forbidden", 403),
    );
    const req = buildRequest("POST", "/api/configure", {
      config_type: "schema",
      name: "test-schema",
    });
    const json = await expectJson(await POST(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Forbidden");
  });

  it("pipeline config_type requires admin — returns 403 for user", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(
      new mocks.MockAuthError("Forbidden", 403),
    );
    const req = buildRequest("POST", "/api/configure", {
      config_type: "pipeline",
      name: "test-pipeline",
    });
    const json = await expectJson(await POST(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Forbidden");
  });

  it("view config_type allows regular user", async () => {
    const req = buildRequest("POST", "/api/configure", {
      config_type: "view",
      name: "my-view",
    });
    const json = await expectJson(await POST(req), 201);
    expect(json.success).toBe(true);
    expect(mocks.mockRequireAuth).toHaveBeenCalled();
    expect(mocks.mockRequireAdmin).not.toHaveBeenCalled();
  });

  it("passes created_by from session user", async () => {
    const req = buildRequest("POST", "/api/configure", {
      config_type: "view",
      name: "my-view",
    });
    await POST(req);
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "ConfigureWorkflow",
      expect.objectContaining({
        args: [expect.objectContaining({ created_by: "user-123" })],
      }),
    );
  });

  it("returns 201 on success", async () => {
    const req = buildRequest("POST", "/api/configure", {
      config_type: "schema",
      name: "new-schema",
      schema_type: "flat",
    });
    const json = await expectJson(await POST(req), 201);
    expect(json.success).toBe(true);
  });

  it("returns 400 when workflow fails", async () => {
    mocks.mockExecute.mockResolvedValue({
      success: false,
      message: "Validation failed",
    });
    const req = buildRequest("POST", "/api/configure", {
      config_type: "view",
      name: "bad-view",
    });
    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
  });
});
