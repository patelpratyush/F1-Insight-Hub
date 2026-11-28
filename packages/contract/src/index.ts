import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

export type { components, paths };
export type DriverStanding = components["schemas"]["DriverStandingOut"];
export type Freshness = components["schemas"]["FreshnessOut"];
export type LiveState = components["schemas"]["LiveStateOut"];
export type DriverTiming = components["schemas"]["DriverTimingOut"];
export type RaceSummary = components["schemas"]["RaceSummary"];
export type RaceDetail = components["schemas"]["RaceDetail"];
export type ResultRow = components["schemas"]["ResultRow"];
export type DriverProfile = components["schemas"]["DriverProfile"];
export type TeamProfile = components["schemas"]["TeamProfile"];
export type SearchHit = components["schemas"]["SearchHit"];
export type ConstructorStanding = components["schemas"]["ConstructorStandingOut"];

export interface ApiClientInit {
  headers?: Record<string, string>;
  fetch?: typeof fetch;
}

export function createApiClient(baseUrl: string, init: ApiClientInit = {}) {
  return createClient<paths>({ baseUrl, ...init });
}
