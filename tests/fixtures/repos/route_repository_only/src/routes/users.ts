import express from "express";
import { UserRepo } from "../repositories/user.repo";

const router = express.Router();
router.get("/users", async (_req, res) => res.json(await UserRepo.list()));

export default router;
