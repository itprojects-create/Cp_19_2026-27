import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Public routes that don't require authentication
  if (
    request.nextUrl.pathname.startsWith('/apply') ||
    request.nextUrl.pathname.startsWith('/verify') ||
    request.nextUrl.pathname === '/' ||
    request.nextUrl.pathname.startsWith('/api') || 
    request.nextUrl.pathname.startsWith('/_next') ||
    request.nextUrl.pathname.includes('.') // static files
  ) {
    return NextResponse.next();
  }

  // Check for session cookie (simplified auth check)
  const sessionCookie = request.cookies.get('session_id');

  // In a real app, we would redirect. For demo simplicity/reliability without backend auth,
  // we might want to be lenient or ensure we have a fallback.
  // For now, follow instructions:
  if (!sessionCookie && request.nextUrl.pathname.startsWith('/dashboard')) {
    // Redirect to login/home if accessing dashboard without session
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
