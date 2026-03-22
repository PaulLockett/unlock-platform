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
  const mockRetrieveView = vi.fn();
  const mockExecute = vi.fn().mockResolvedValue({ success: true });
  const mockGetTemporalClient = vi.fn().mockResolvedValue({
    workflow: { execute: mockExecute },
  });
  const mockUser = { id: "user-123", email: "testuser@example.com", role: "user" };
  const mockAdmin = { id: "admin-456", email: "admin@example.com", role: "admin" };
  return {
    MockAuthError, mockGetSessionUser, mockRequireAuth,
    mockRetrieveView, mockExecute, mockGetTemporalClient,
    mockUser, mockAdmin,
  };
});

vi.mock("@/lib/auth/session", () => ({
  getSessionUser: mocks.mockGetSessionUser,
  requireAuth: mocks.mockRequireAuth,
  AuthError: mocks.MockAuthError,
}));
vi.mock("@/lib/redis/views", () => ({
  retrieveView: mocks.mockRetrieveView,
}));
vi.mock("@/lib/temporal/client", () => ({
  getTemporalClient: mocks.mockGetTemporalClient,
  TASK_QUEUES: { DATA_MANAGER: "data-manager-queue", CONFIG_ACCESS: "config-access-queue" },
}));

import { GET, PATCH } from "./route";

function makeParams(shareToken: string) {
  return Promise.resolve({ shareToken });
}

const baseView = {
  name: "My View",
  created_by: "user-123",
  visibility: "public",
  schema_id: "s-1",
  filters: {},
  layout_config: {},
  description: "",
};

describe("GET /api/views/[shareToken]", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 404 when view not found", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: false,
      message: "View not found",
    });

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 404);

    expect(json.success).toBe(false);
    expect(json.message).toBe("View not found");
  });

  it("returns public view without auth", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, visibility: "public" },
    });
    mocks.mockGetSessionUser.mockResolvedValue(null);

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
    expect(mocks.mockGetSessionUser).not.toHaveBeenCalled();
  });

  it("returns 401 for private view when not authenticated", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, visibility: "private" },
    });
    mocks.mockGetSessionUser.mockResolvedValue(null);

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 401);

    expect(json.success).toBe(false);
    expect(json.message).toBe("Authentication required for this view");
  });

  it("returns private view when authenticated", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, visibility: "private" },
    });
    mocks.mockGetSessionUser.mockResolvedValue(mocks.mockUser);

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
  });

  it("returns 200 with public Cache-Control for public view", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, visibility: "public" },
    });

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    await expectJson(res, 200);

    expect(res.headers.get("Cache-Control")).toBe(
      "public, max-age=120, stale-while-revalidate=300",
    );
  });

  it("returns private Cache-Control for private view", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, visibility: "private" },
    });
    mocks.mockGetSessionUser.mockResolvedValue(mocks.mockUser);

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    await expectJson(res, 200);

    expect(res.headers.get("Cache-Control")).toBe(
      "private, max-age=60, stale-while-revalidate=120",
    );
  });

  it("returns 500 when read errors", async () => {
    mocks.mockRetrieveView.mockResolvedValue({
      success: false,
      message: "Internal workflow failure",
    });

    const req = buildRequest("GET", "/api/views/tok-abc");
    const res = await GET(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 500);

    expect(json.success).toBe(false);
  });
});

describe("PATCH /api/views/[shareToken]", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAuth.mockRejectedValue(
      new mocks.MockAuthError("Not authenticated", 401),
    );

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 401);

    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 400 on invalid body", async () => {
    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 400);

    expect(json.success).toBe(false);
  });

  it("returns 404 when view not found", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRetrieveView.mockResolvedValue({
      success: false,
      view: null,
    });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 404);

    expect(json.success).toBe(false);
    expect(json.message).toBe("View not found");
  });

  it("returns 403 when user lacks write permission", async () => {
    const otherUser = { id: "other-789", email: "other@example.com", role: "user" };
    mocks.mockRequireAuth.mockResolvedValue(otherUser);
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, created_by: "user-123" },
      permissions: [],
    });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 403);

    expect(json.success).toBe(false);
    expect(json.message).toBe("Write access required");
  });

  it("allows owner to patch", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, created_by: "user-123" },
      permissions: [],
    });
    mocks.mockExecute.mockResolvedValueOnce({ success: true, message: "updated" });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
    expect(mocks.mockExecute).toHaveBeenCalledTimes(1);
  });

  it("allows user with write permission to patch", async () => {
    const writeUser = { id: "writer-999", email: "writer@example.com", role: "user" };
    mocks.mockRequireAuth.mockResolvedValue(writeUser);
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, created_by: "user-123" },
      permissions: [{ principal_id: "writer-999", permission: "write" }],
    });
    mocks.mockExecute.mockResolvedValueOnce({ success: true, message: "updated" });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
  });

  it("allows admin to patch any view", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockAdmin);
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, created_by: "user-123" },
      permissions: [],
    });
    mocks.mockExecute.mockResolvedValueOnce({ success: true, message: "updated" });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Admin Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
  });

  it("returns 200 on successful update", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, created_by: "user-123" },
      permissions: [],
    });
    mocks.mockExecute.mockResolvedValueOnce({ success: true, message: "updated", view: { name: "New Name" } });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "New Name" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
    expect(json.message).toBe("updated");
  });

  it("returns 400 when ConfigureWorkflow fails", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockRetrieveView.mockResolvedValue({
      success: true,
      view: { ...baseView, created_by: "user-123" },
      permissions: [],
    });
    mocks.mockExecute.mockResolvedValueOnce({ success: false, message: "configuration error" });

    const req = buildRequest("PATCH", "/api/views/tok-abc", { name: "Updated" });
    const res = await PATCH(req, { params: makeParams("tok-abc") });
    const json = await expectJson(res, 400);

    expect(json.success).toBe(false);
    expect(json.message).toBe("configuration error");
  });
});
