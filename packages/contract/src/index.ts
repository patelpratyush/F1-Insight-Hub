import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

export type { components, paths };
export type DriverStanding = components["schemas"]["DriverStandingOut"];
export type Freshness = components["schemas"]["FreshnessOut"];
export type LiveState = components["schemas"]["LiveStateOut"];
export type DriverTiming = components["schemas"]["DriverTimingOut"];

export interface ApiClientInit {
  headers?: Record<string, string>;
  fetch?: typeof fetch;
}

export function createApiClient(baseUrl: string, init: ApiClientInit = {}) {
  return createClient<paths>({ baseUrl, ...init });
}
