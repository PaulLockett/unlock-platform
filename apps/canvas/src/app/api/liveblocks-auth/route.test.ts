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
  const mockUser = { id: "user-123", email: "testuser@example.com", role: "user" };
  return { MockAuthError, mockGetSessionUser, mockRequireAuth, mockRequireAdmin, mockUser };
});

vi.mock("@/lib/auth/session", () => ({
  getSessionUser: mocks.mockGetSessionUser,
  requireAuth: mocks.mockRequireAuth,
  requireAdmin: mocks.mockRequireAdmin,
  AuthError: mocks.MockAuthError,
}));

import { POST } from "./route";

describe("POST /api/liveblocks-auth", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    process.env.LIVEBLOCKS_SECRET_KEY = "sk-test-secret";
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ token: "lb-test-token" }),
      text: async () => "ok",
    }));
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAuth.mockRejectedValue(new mocks.MockAuthError("Not authenticated", 401));
    const req = buildRequest("POST", "/api/liveblocks-auth", { room: "room-1" });
    const json = await expectJson(await POST(req), 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 400 when room is missing", async () => {
    const req = buildRequest("POST", "/api/liveblocks-auth", {});
    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Room ID required");
  });

  it("returns 503 when LIVEBLOCKS_SECRET_KEY is not set", async () => {
    delete process.env.LIVEBLOCKS_SECRET_KEY;
    const req = buildRequest("POST", "/api/liveblocks-auth", { room: "room-1" });
    const json = await expectJson(await POST(req), 503);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Liveblocks not configured");
  });

  it("returns Liveblocks token on success", async () => {
    const req = buildRequest("POST", "/api/liveblocks-auth", { room: "room-1" });
    const json = await expectJson(await POST(req), 200);
    expect(json.token).toBe("lb-test-token");
  });

  it("returns error status when Liveblocks API returns non-ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({}),
      text: async () => "Forbidden",
    }));
    const req = buildRequest("POST", "/api/liveblocks-auth", { room: "room-1" });
    const json = await expectJson(await POST(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Liveblocks authorization failed");
  });

  it("passes correct userId and userInfo to Liveblocks", async () => {
    const req = buildRequest("POST", "/api/liveblocks-auth", { room: "my-room" });
    await POST(req);

    const fetchMock = vi.mocked(globalThis.fetch);
    expect(fetchMock).toHaveBeenCalledOnce();

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("https://api.liveblocks.io/v2/rooms/my-room/authorize");
    expect(options?.method).toBe("POST");
    expect(options?.headers).toEqual(
      expect.objectContaining({
        Authorization: "Bearer sk-test-secret",
        "Content-Type": "application/json",
      }),
    );

    const body = JSON.parse(options?.body as string);
    expect(body).toEqual({
      userId: "user-123",
      userInfo: { name: "testuser", email: "testuser@example.com" },
    });
  });
});
