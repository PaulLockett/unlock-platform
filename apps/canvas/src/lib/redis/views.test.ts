import { describe, it, expect, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => {
  const mockSmembers = vi.fn().mockResolvedValue([]);
  const mockGet = vi.fn().mockResolvedValue(null);
  const mockHgetall = vi.fn().mockResolvedValue(null);
  const mockPipelineGet = vi.fn();
  const mockPipelineExec = vi.fn().mockResolvedValue([]);
  const mockPipeline = vi.fn().mockReturnValue({
    get: mockPipelineGet,
    exec: mockPipelineExec,
  });
  const mockRedis = {
    smembers: mockSmembers,
    get: mockGet,
    hgetall: mockHgetall,
    pipeline: mockPipeline,
  };
  return {
    mockSmembers, mockGet, mockHgetall,
    mockPipelineGet, mockPipelineExec, mockPipeline, mockRedis,
  };
});

vi.mock("./client", () => ({
  getRedisClient: () => mocks.mockRedis,
  keys: {
    view: (id: string) => `cfg:view:${id}`,
    viewIdxStatus: (s: string) => `cfg:view:idx:status:${s}`,
    viewIdxToken: (t: string) => `cfg:view:idx:token:${t}`,
    schema: (id: string) => `cfg:schema:${id}`,
    perm: (id: string) => `cfg:perm:${id}`,
  },
}));

import { listActiveViews, retrieveView } from "./views";

describe("listActiveViews", () => {
  beforeEach(() => vi.clearAllMocks());

  it("returns empty when no active views", async () => {
    mocks.mockSmembers.mockResolvedValue([]);
    const result = await listActiveViews("u-1", "user");
    expect(result).toEqual({ success: true, items: [] });
  });

  it("filters views for regular user (only own)", async () => {
    mocks.mockSmembers.mockResolvedValue(["v-1", "v-2"]);
    mocks.mockPipelineExec.mockResolvedValue([
      { id: "v-1", created_by: "u-1", name: "Mine" },
      { id: "v-2", created_by: "u-other", name: "Theirs" },
    ]);

    const result = await listActiveViews("u-1", "user");
    expect(result.items).toHaveLength(1);
    expect(result.items[0].id).toBe("v-1");
  });

  it("returns all views for admin", async () => {
    mocks.mockSmembers.mockResolvedValue(["v-1", "v-2"]);
    mocks.mockPipelineExec.mockResolvedValue([
      { id: "v-1", created_by: "u-1" },
      { id: "v-2", created_by: "u-other" },
    ]);

    const result = await listActiveViews("admin-1", "admin");
    expect(result.items).toHaveLength(2);
  });

  it("skips null results from pipeline", async () => {
    mocks.mockSmembers.mockResolvedValue(["v-1", "v-deleted"]);
    mocks.mockPipelineExec.mockResolvedValue([
      { id: "v-1", created_by: "u-1" },
      null,
    ]);

    const result = await listActiveViews("u-1", "user");
    expect(result.items).toHaveLength(1);
  });
});

describe("retrieveView", () => {
  beforeEach(() => vi.clearAllMocks());

  it("returns not found when token has no view", async () => {
    mocks.mockGet.mockResolvedValue(null);
    const result = await retrieveView("bad-token");
    expect(result.success).toBe(false);
    expect(result.message).toBe("View not found");
  });

  it("returns not found when view ID exists but view deleted", async () => {
    mocks.mockGet
      .mockResolvedValueOnce("v-1")    // token → viewId
      .mockResolvedValueOnce(null);     // viewId → null (deleted)

    const result = await retrieveView("tok-abc");
    expect(result.success).toBe(false);
    expect(result.message).toBe("View not found");
  });

  it("returns view, schema, and permissions on success", async () => {
    const view = { id: "v-1", schema_id: "s-1", name: "Test" };
    const schema = { id: "s-1", fields: [] };

    mocks.mockGet
      .mockResolvedValueOnce("v-1")     // token → viewId
      .mockResolvedValueOnce(view)       // viewId → view
      .mockResolvedValueOnce(schema);    // schemaId → schema

    mocks.mockHgetall.mockResolvedValue({
      "u-1": JSON.stringify({ permission: "write" }),
    });

    const result = await retrieveView("tok-abc");
    expect(result.success).toBe(true);
    expect(result.view).toEqual(view);
    expect(result.schema).toEqual(schema);
    expect(result.permissions).toEqual([
      { principal_id: "u-1", permission: "write" },
    ]);
  });

  it("returns empty permissions when no perm hash", async () => {
    mocks.mockGet
      .mockResolvedValueOnce("v-1")
      .mockResolvedValueOnce({ id: "v-1", name: "No Perms" });

    mocks.mockHgetall.mockResolvedValue(null);

    const result = await retrieveView("tok-abc");
    expect(result.success).toBe(true);
    expect(result.permissions).toEqual([]);
  });
});
