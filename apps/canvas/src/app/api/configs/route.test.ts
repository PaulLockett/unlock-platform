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
  const mockRequireAuth = vi.fn();
  const mockRequireAdmin = vi.fn();
  const mockSurveyConfigs = vi.fn().mockResolvedValue({ success: true, items: [] });
  const mockUser = { id: "user-123", email: "testuser@example.com", role: "user" };
  const mockAdmin = { id: "admin-456", email: "admin@example.com", role: "admin" };
  return {
    MockAuthError, mockRequireAuth, mockRequireAdmin,
    mockSurveyConfigs, mockUser, mockAdmin,
  };
});

vi.mock("@/lib/auth/session", () => ({
  requireAuth: mocks.mockRequireAuth,
  requireAdmin: mocks.mockRequireAdmin,
  AuthError: mocks.MockAuthError,
}));
vi.mock("@/lib/redis/configs", () => ({
  surveyConfigs: mocks.mockSurveyConfigs,
}));

import { GET } from "./route";

describe("GET /api/configs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockSurveyConfigs.mockResolvedValue({ success: true, items: [] });
  });

  it("defaults to type=schema when no query param", async () => {
    const req = buildRequest("GET", "/api/configs");
    await GET(req);
    expect(mocks.mockRequireAdmin).toHaveBeenCalled();
    expect(mocks.mockSurveyConfigs).toHaveBeenCalledWith({
      configType: "schema",
      status: null,
      namePattern: null,
      limit: 100,
      offset: 0,
    });
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

  it("passes query params to surveyConfigs", async () => {
    const req = buildRequest(
      "GET",
      "/api/configs?type=view&status=active&name=test&limit=50&offset=10",
    );
    await GET(req);
    expect(mocks.mockSurveyConfigs).toHaveBeenCalledWith({
      configType: "view",
      status: "active",
      namePattern: "test",
      limit: 50,
      offset: 10,
    });
  });

  it("returns 200 on success with Cache-Control", async () => {
    const req = buildRequest("GET", "/api/configs?type=schema");
    const res = await GET(req);
    const json = await expectJson(res, 200);
    expect(json.success).toBe(true);
    expect(res.headers.get("Cache-Control")).toBe("private, max-age=60");
  });

  it("returns 500 when read fails", async () => {
    mocks.mockSurveyConfigs.mockResolvedValue({
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
