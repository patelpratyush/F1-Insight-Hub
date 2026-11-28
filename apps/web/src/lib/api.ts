import { createApiClient } from "@f1/contract";
import { env } from "./env";

export function getApi(token?: string) {
  return createApiClient(env.API_BASE_URL, token ? { headers: { Authorization: `Bearer ${token}` } } : {});
}

/** Public data: Next caches the response and revalidates it every 60 s. */
export const PUBLIC = { next: { revalidate: 60 } };
