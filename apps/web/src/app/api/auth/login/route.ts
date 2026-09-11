import { NextRequest, NextResponse } from 'next/server';
import { timingSafeEqual } from 'crypto';
import { createSessionToken, SESSION_COOKIE, SESSION_MAX_AGE } from '@/lib/auth/session';

export const runtime = 'nodejs';

function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) return false;
  return timingSafeEqual(ab, bb);
}

export async function POST(req: NextRequest) {
  let body: { email?: string; password?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid request body' }, { status: 400 });
  }

  const email = (body.email ?? '').trim().toLowerCase();
  const password = body.password ?? '';

  const adminEmail = (process.env.ADMIN_EMAIL ?? '').trim().toLowerCase();
  const adminPassword = process.env.ADMIN_PASSWORD ?? '';

  if (!email || !password) {
    return NextResponse.json({ ok: false, error: 'Email and password are required' }, { status: 400 });
  }

  // Constant-time-ish comparison to avoid trivial timing leaks.
  const emailOk = adminEmail && safeEqual(email, adminEmail);
  const passOk = adminPassword && safeEqual(password, adminPassword);

  if (!emailOk || !passOk) {
    return NextResponse.json({ ok: false, error: 'Invalid email or password' }, { status: 401 });
  }

  const token = await createSessionToken(adminEmail);

  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: SESSION_MAX_AGE
  });
  return res;
}
