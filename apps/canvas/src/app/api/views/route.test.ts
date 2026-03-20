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

describe("GET /api/views", () => {
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

    const res = await GET();
    const json = await expectJson(res, 401);

    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("admin sees all views (created_by is null)", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({ success: true, views: [] });

    await GET();

    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "SurveyConfigsWorkflow",
      expect.objectContaining({
        args: [{ config_type: "view", status: "active", created_by: null }],
      }),
    );
  });

  it("regular user sees only own views (created_by is user.id)", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockExecute.mockResolvedValue({ success: true, views: [] });

    await GET();

    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "SurveyConfigsWorkflow",
      expect.objectContaining({
        args: [{ config_type: "view", status: "active", created_by: "user-123" }],
      }),
    );
  });

  it("returns 200 on success", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockExecute.mockResolvedValue({ success: true, views: [{ id: "v-1" }] });

    const res = await GET();
    const json = await expectJson(res, 200);

    expect(json.success).toBe(true);
    expect(json.views).toEqual([{ id: "v-1" }]);
  });

  it("returns 500 when workflow fails", async () => {
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockExecute.mockResolvedValue({ success: false, message: "workflow error" });

    const res = await GET();
    const json = await expectJson(res, 500);

    expect(json.success).toBe(false);
    expect(json.message).toBe("workflow error");
  });
});
