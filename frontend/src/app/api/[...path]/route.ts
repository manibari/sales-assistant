import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8002";

/**
 * Catch-all API proxy route.
 *
 * Forwards /api/* requests to the FastAPI backend.
 *
 * Trailing slash is added only for GET requests — FastAPI collection routes
 * (GET /clients/, GET /deals/, etc.) require it. POST/PUT/PATCH/DELETE routes
 * must NOT get a trailing slash as FastAPI's redirect_slashes would 307-redirect
 * them, and the redirect can't resend the request body.
 */
async function proxy(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const { search } = new URL(request.url);

  const isBodyMethod = ["POST", "PUT", "PATCH"].includes(request.method);

  // Only GET requests get the trailing slash (needed for FastAPI collection routes)
  const trailingSlash = request.method === "GET" ? "/" : "";
  const targetUrl = `${BACKEND_URL}/api/${path.join("/")}${trailingSlash}${search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");

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
