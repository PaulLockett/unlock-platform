import { vi } from "vitest";

let _nextFetchResponse: { status: number; body: unknown } = {
  status: 200,
  body: { token: "test-liveblocks-token" },
};

/**
 * Set the next global fetch() return value.
 */
export function mockFetchResponse(status: number, body: unknown) {
  _nextFetchResponse = { status, body };
}

/**
 * Reset fetch mock state.
 */
export function resetFetchMock() {
  _nextFetchResponse = {
    status: 200,
    body: { token: "test-liveblocks-token" },
  };
}

/**
 * Install the global fetch mock. Call in beforeEach.
 */
export function installFetchMock() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async () => ({
      ok: _nextFetchResponse.status >= 200 && _nextFetchResponse.status < 300,
      status: _nextFetchResponse.status,
      json: async () => _nextFetchResponse.body,
      text: async () => JSON.stringify(_nextFetchResponse.body),
    })),
  );
}
