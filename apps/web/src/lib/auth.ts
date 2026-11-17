import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins";
import { nextCookies } from "better-auth/next-js";
import { Pool } from "pg";
import { env } from "./env";

export const auth = betterAuth({
  database: new Pool({ connectionString: env.AUTH_DATABASE_URL }),
  secret: env.BETTER_AUTH_SECRET,
  baseURL: env.BETTER_AUTH_URL,
  emailAndPassword: { enabled: true, requireEmailVerification: false, minPasswordLength: 10 },
  socialProviders: {
    ...(env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET
      ? { google: { clientId: env.GOOGLE_CLIENT_ID, clientSecret: env.GOOGLE_CLIENT_SECRET } } : {}),
    ...(env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET
      ? { github: { clientId: env.GITHUB_CLIENT_ID, clientSecret: env.GITHUB_CLIENT_SECRET } } : {}),
  },
  rateLimit: { enabled: true, window: 60, max: 30 },
  plugins: [jwt({ jwt: { issuer: env.BETTER_AUTH_URL, expirationTime: "10m" } }), nextCookies()],
});
