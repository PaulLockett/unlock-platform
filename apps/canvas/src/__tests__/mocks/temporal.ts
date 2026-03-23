import { vi } from "vitest";

let _nextResult: Record<string, unknown> = { success: true };
let _nextError: Error | null = null;
let _lastCall: { workflowName: string; options: Record<string, unknown> } | null = null;

export function mockWorkflowResult(data: Record<string, unknown>) {
  _nextResult = data;
  _nextError = null;
}

export function mockWorkflowError(err: Error) {
  _nextError = err;
  _nextResult = {};
}

export function getLastWorkflowCall() {
  return _lastCall;
}

export function resetTemporalMock() {
  _nextResult = { success: true };
  _nextError = null;
  _lastCall = null;
}

// The mock execute function — shared across all test files
export const mockExecute = vi.fn().mockImplementation(
  async (workflowName: string, options: Record<string, unknown>) => {
    _lastCall = { workflowName, options };
    if (_nextError) throw _nextError;
    return _nextResult;
  },
);

export const mockGetTemporalClient = vi.fn().mockImplementation(async () => ({
  workflow: { execute: mockExecute },
}));
