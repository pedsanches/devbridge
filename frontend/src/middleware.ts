import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
    // Get the pathname of the request
    const path = request.nextUrl.pathname;

    // Define public paths that don't require authentication
    const isPublicPath = path === "/login" || path === "/auth/verify" || path === "/";

    // Get the token from the cookies
    const token = request.cookies.get("session")?.value || "";

    // Protected routes pattern
    const isProtectedRoute =
        path.startsWith("/dashboard") ||
        path.startsWith("/chat") ||
        path.startsWith("/teams") ||
        path.startsWith("/metrics") ||
        path.startsWith("/reports") ||
        path.startsWith("/settings");

    // Redirect logic
    if (isProtectedRoute && !token) {
        return NextResponse.redirect(new URL("/login", request.nextUrl));
    }

    if (isPublicPath && token && path !== "/") {
        // Optional: Redirect to dashboard if already logged in and trying to access login
        // return NextResponse.redirect(new URL("/dashboard", request.nextUrl));
    }

    return NextResponse.next();
}

// Configure paths that match the middleware
export const config = {
    matcher: [
        "/dashboard/:path*",
        "/chat/:path*",
        "/teams/:path*",
        "/metrics/:path*",
        "/reports/:path*",
        "/settings/:path*",
        "/login",
        "/auth/verify",
    ],
};
