import request from "supertest";

describe("users", () => {
  it("works", async () => {
    await request("http://localhost").get("/users");
  });
});
