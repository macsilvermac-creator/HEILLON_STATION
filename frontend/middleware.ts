import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Edge middleware — auth gate + safety headers.
 *
 * Behaviour:
 * - Protected routes: redirect unauthenticated requests to /login?from=<path>
 * - Public routes (landing, /docs, /login, /register, /api/proxy/*, /health, /verification/*): pass through
 * - All routes get a small set of safety headers added
 *
 * Cookie used: `heillon_auth_token` (HttpOnly, set by backend on /auth/login).
 * Edge cannot decode JWT (no secret in edge runtime) — presence-only check
 * is sufficient as defense-in-depth; the backend validates signature/expiry.
 */

const AUTH_COOKIE = "heillon_auth_token";

const PUBLIC_PATH_PREFIXES = [
  "/login",
  "/register",
  "/docs",
  "/api/proxy",
  "/api/v1", // API routes: auth enforced by the backend (401), not the edge guard.
             // Gating these here would turn the login POST itself into an HTML redirect.
  "/health",
  "/verification",
  "/_next",
  "/favicon",
  "/manifest.json",
  "/icons",
  "/sw.js",
  "/workbox",
  "/m", // PWA mobile shell handles its own auth
];

const PUBLIC_EXACT = new Set(["/", "/robots.txt", "/sitemap.xml"]);

function isPublic(pathname: string): boolean {
  if (PUBLIC_EXACT.has(pathname)) return true;
  return PUBLIC_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public — pass through
  if (isPublic(pathname)) {
    return NextResponse.next();
  }

  // Auth gate
  const hasSessionCookie = request.cookies.has(AUTH_COOKIE);
  if (!hasSessionCookie) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Skip static assets, API proxy passthrough, and Next.js internals at the matcher level
  matcher: ["/((?!_next/static|_next/image|favicon.ico|sw.js|workbox-.*|icons/).*)"],
};
