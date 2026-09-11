import { Pool } from 'pg';

// Server-only Postgres access for the admin console. This reads the same
// POSTGRES_URL that the Flask API uses, so the live "old database" is what
// the console displays — no local API required.
const connectionString = process.env.POSTGRES_URL;

if (!connectionString) {
  // Surface early during build/runtime rather than on first query.
  console.error('POSTGRES_URL is not set — admin console cannot reach the database.');
}

const globalForPg = globalThis as unknown as { __xSuitePool?: Pool };

export const pool =
  globalForPg.__xSuitePool ??
  new Pool({
    connectionString,
    max: 3,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 15_000
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPg.__xSuitePool = pool;
}

export interface QueryRow {
  [column: string]: unknown;
}

export async function query<T = QueryRow>(sql: string, params: unknown[] = []): Promise<T[]> {
  const res = await pool.query(sql, params);
  return res.rows as T[];
}

export async function queryOne<T = QueryRow>(sql: string, params: unknown[] = []): Promise<T | null> {
  const rows = await query<T>(sql, params);
  return rows[0] ?? null;
}
