const request = require("supertest");

describe("health", () => {
  it("works", async () => {
    await request("http://localhost").get("/health");
  });
});
