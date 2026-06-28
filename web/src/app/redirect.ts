import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Redirect root to Arabic locale
  if (request.nextUrl.pathname === "/") {
    return NextResponse.redirect(new URL("/ar", request.url));
  }
}

