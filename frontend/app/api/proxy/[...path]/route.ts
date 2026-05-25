import { type NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND = (
  process.env.BACKEND_PROXY_TARGET ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
]);

function forwardHeaders(req: NextRequest, cookieHeader: string): Headers {
  const out = new Headers();
  for (const [k, v] of req.headers.entries()) {
    if (!HOP_BY_HOP.has(k.toLowerCase())) {
      out.set(k, v);
    }
  }
  if (cookieHeader) {
    out.set("cookie", cookieHeader);
  }
  return out;
}

async function handle(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const upstreamPath = path.join("/");
  const search = req.nextUrl.search ?? "";
  const url = `${BACKEND}/api/v1/${upstreamPath}${search}`;

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const headers = forwardHeaders(req, cookieHeader);

  let body: BodyInit | undefined;
  const method = req.method.toUpperCase();
  if (!["GET", "HEAD"].includes(method)) {
    body = await req.arrayBuffer();
  }

  const upstream = await fetch(url, {
    method,
    headers,
    body,
    redirect: "manual",
    // @ts-expect-error — Node 18+ supports duplex for streaming bodies
    duplex: body ? "half" : undefined,
  });

  const responseHeaders = new Headers();
  for (const [k, v] of upstream.headers.entries()) {
    if (!HOP_BY_HOP.has(k.toLowerCase())) {
      responseHeaders.append(k, v);
    }
  }

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const HEAD = handle;
export const OPTIONS = handle;

export const dynamic = "force-dynamic";
