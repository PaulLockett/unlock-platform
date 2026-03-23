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
  const mockRequireAuth = vi.fn();
  const mockListActiveViews = vi.fn().mockResolvedValue({ success: true, items: [] });
  const mockUser = { id: "user-123", email: "testuser@example.com", role: "user" };
  const mockAdmin = { id: "admin-456", email: "admin@example.com", role: "admin" };
  return {
    MockAuthError, mockRequireAuth, mockListActiveViews, mockUser, mockAdmin,
  };
});

vi.mock("@/lib/auth/session", () => ({
  requireAuth: mocks.mockRequireAuth,
  AuthError: mocks.MockAuthError,
}));
vi.mock("@/lib/redis/views", () => ({
  listActiveViews: mocks.mockListActiveViews,
}));

import { GET } from "./route";

describe("GET /api/views", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAuth.mockRejectedValue(
      new mocks.MockAuthError("Not authenticated", 401),
    );

    const res = await GET();
    const json = await expectJson(res, 401);

    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("admin sees all views (role=admin)", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockAdmin);
    mocks.mockListActiveViews.mockResolvedValue({ success: true, items: [] });

    await GET();

    expect(mocks.mockListActiveViews).toHaveBeenCalledWith("admin-456", "admin");
  });

  it("regular user passes own id and role", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockListActiveViews.mockResolvedValue({ success: true, items: [] });

    await GET();

    expect(mocks.mockListActiveViews).toHaveBeenCalledWith("user-123", "user");
  });

  it("returns 200 on success with Cache-Control", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockListActiveViews.mockResolvedValue({
      success: true,
      items: [{ id: "v-1" }],
    });

    const res = await GET();
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
    expect(json.items).toEqual([{ id: "v-1" }]);
    expect(res.headers.get("Cache-Control")).toBe(
      "private, max-age=30, stale-while-revalidate=60",
    );
  });

  it("returns 500 when read fails", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockListActiveViews.mockResolvedValue({
      success: false,
      message: "redis error",
    });

    const res = await GET();
    const json = await expectJson(res, 500);

    expect(json.success).toBe(false);
  });
});
