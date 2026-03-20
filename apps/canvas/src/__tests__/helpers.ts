import { NextRequest } from "next/server";
import { expect } from "vitest";

/**
 * Build a NextRequest for testing API routes.
 */
export function buildRequest(
  method: string,
  url: string,
  body?: Record<string, unknown>,
): NextRequest {
  const init: RequestInit = { method };
  if (body) {
    init.body = JSON.stringify(body);
    init.headers = { "Content-Type": "application/json" };
  }
  return new NextRequest(new URL(url, "http://localhost:3000"), init);
}

/**
 * Build a NextRequest with FormData body.
 */
export function buildFormDataRequest(
  url: string,
  formData: FormData,
): NextRequest {
  return new NextRequest(new URL(url, "http://localhost:3000"), {
    method: "POST",
    body: formData,
  });
}

/**
 * Assert response status and parse JSON body.
 */
export async function expectJson(
  response: Response,
  status: number,
): Promise<Record<string, unknown>> {
  expect(response.status).toBe(status);
  const json = await response.json();
  return json as Record<string, unknown>;
}
