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

import { GET } from "./route";

describe("GET /api/configs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({ success: true, data: [] });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("defaults to type=schema when no query param", async () => {
    const req = buildRequest("GET", "/api/configs");
    await GET(req);
    expect(mocks.mockRequireAdmin).toHaveBeenCalled();
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "SurveyConfigsWorkflow",
      expect.objectContaining({
        args: [expect.objectContaining({ config_type: "schema" })],
      }),
    );
  });

  it("schema type requires admin — returns 403 for user", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(
      new mocks.MockAuthError("Forbidden", 403),
    );
    const req = buildRequest("GET", "/api/configs?type=schema");
    const json = await expectJson(await GET(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Forbidden");
  });

  it("pipeline type requires admin — returns 403 for user", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(
      new mocks.MockAuthError("Forbidden", 403),
    );
    const req = buildRequest("GET", "/api/configs?type=pipeline");
    const json = await expectJson(await GET(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Forbidden");
  });

  it("non-schema/pipeline type allows regular user", async () => {
    const req = buildRequest("GET", "/api/configs?type=view");
    const json = await expectJson(await GET(req), 200);
    expect(json.success).toBe(true);
    expect(mocks.mockRequireAuth).toHaveBeenCalled();
    expect(mocks.mockRequireAdmin).not.toHaveBeenCalled();
  });

  it("passes query params to workflow args", async () => {
    const req = buildRequest(
      "GET",
      "/api/configs?type=view&status=active&name=test&limit=50&offset=10",
    );
    await GET(req);
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "SurveyConfigsWorkflow",
      expect.objectContaining({
        args: [
          {
            config_type: "view",
            status: "active",
            name_pattern: "test",
            limit: 50,
            offset: 10,
          },
        ],
      }),
    );
  });

  it("returns 200 on success", async () => {
    const req = buildRequest("GET", "/api/configs?type=schema");
    const json = await expectJson(await GET(req), 200);
    expect(json.success).toBe(true);
  });

  it("returns 500 when workflow fails", async () => {
    mocks.mockExecute.mockResolvedValue({
      success: false,
      message: "Database error",
    });
    const req = buildRequest("GET", "/api/configs?type=view");
    const json = await expectJson(await GET(req), 500);
    expect(json.success).toBe(false);
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAuth.mockRejectedValue(
      new mocks.MockAuthError("Unauthorized", 401),
    );
    const req = buildRequest("GET", "/api/configs?type=view");
    const json = await expectJson(await GET(req), 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Unauthorized");
  });
});
