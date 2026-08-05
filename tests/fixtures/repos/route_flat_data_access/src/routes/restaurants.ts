import express from "express";
import { redisClient } from "../utils/client";

const router = express.Router();
router.get("/restaurants", async (_req, res) => res.json(await redisClient.keys("restaurant:*")));

export default router;
