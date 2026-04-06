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
  try {
  const { path } = await params;
  const { search } = new URL(request.url);

  const isBodyMethod = ["POST", "PUT", "PATCH"].includes(request.method);

  // Only GET requests get the trailing slash (needed for FastAPI collection routes)
  const trailingSlash = request.method === "GET" ? "/" : "";
  const targetUrl = `${BACKEND_URL}/api/${path.join("/")}${trailingSlash}${search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");

  // Read body as ArrayBuffer to avoid ReadableStream issues in Next.js 15
  let body: ArrayBuffer | undefined;
  if (isBodyMethod) {
    body = await request.arrayBuffer();
  }

  let response: Response;
  try {
    response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: body,
    });
  } catch (err) {
    console.error("[proxy] fetch error:", targetUrl, err);
    return new NextResponse("Backend unreachable", { status: 502 });
  }

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("transfer-encoding");
  // Stream the response body back (handles cookies, binary, JSON equally)
  const responseBody = await response.arrayBuffer();

  return new NextResponse(responseBody, {
    status: response.status,
    headers: responseHeaders,
  });
  } catch (err) {
    console.error("[proxy] unhandled error:", err);
    return new NextResponse(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
