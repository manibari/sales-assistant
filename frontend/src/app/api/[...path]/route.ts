import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8002";

/**
 * Catch-all API proxy route.
 *
 * Forwards /api/* requests to the FastAPI backend, always with a trailing
 * slash before the query string (FastAPI collection routes require it, and
 * Next.js strips it during request normalization).
 */
async function proxy(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const { search } = new URL(request.url);

  // Always add trailing slash before the query string
  const targetUrl = `${BACKEND_URL}/api/${path.join("/")}/${search}`;

  const headers = new Headers(request.headers);
  // Remove headers that shouldn't be forwarded
  headers.delete("host");
  headers.delete("connection");

  const isBodyMethod = ["POST", "PUT", "PATCH"].includes(request.method);

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body: isBodyMethod ? request.body : undefined,
    // @ts-expect-error — Node.js fetch supports duplex for streaming
    duplex: isBodyMethod ? "half" : undefined,
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("transfer-encoding");

  return new NextResponse(response.body, {
    status: response.status,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
