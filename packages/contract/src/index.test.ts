import { describe, expect, it } from "vitest";
import { createApiClient } from "./index";

describe("createApiClient", () => {
  it("calls the typed standings endpoint with the season query", async () => {
    let url = "";
    const client = createApiClient("http://api.test", {
      fetch: async (req) => {
        url = (req as Request).url;
        return new Response("[]", { headers: { "content-type": "application/json" } });
      },
    });
    const { data } = await client.GET("/v1/standings/drivers", { params: { query: { season: 2025 } } });
    expect(url).toBe("http://api.test/v1/standings/drivers?season=2025");
    expect(data).toEqual([]);
  });
});
