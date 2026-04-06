import { NextResponse, type NextRequest } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL ?? "http://127.0.0.1:8002";

/**
 * Proxy /api/* to the backend with trailing-slash normalization.
 *
 * Next.js strips trailing slashes from URL paths before query strings
 * (e.g. /api/nx/deals/?view=urgency → /api/nx/deals?view=urgency).
 * FastAPI routes expect trailing slashes. This middleware rewrites all
 * /api/* requests directly to the backend, adding the trailing slash
 * so FastAPI route matching works correctly.
 */
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (pathname.startsWith("/api/")) {
    // Next.js strips trailing slashes before query strings, e.g.
    //   /api/nx/deals/?view=urgency → /api/nx/deals?view=urgency
    // FastAPI routes expect trailing slashes on collection endpoints.
    // Heuristic: restore the slash only when a query string is present
    // and the last path segment looks like a named resource (not a numeric ID).
    const lastSegment = pathname.split("/").filter(Boolean).pop() ?? "";
    const isNumericId = /^\d+$/.test(lastSegment);
    const needsSlash =
      !pathname.endsWith("/") && !isNumericId && search.length > 0;
    const normalizedPath = needsSlash ? pathname + "/" : pathname;
    const target = `${BACKEND_URL}${normalizedPath}${search}`;
    return NextResponse.rewrite(target);
  }
}

export const config = {
  matcher: "/api/:path*",
};
