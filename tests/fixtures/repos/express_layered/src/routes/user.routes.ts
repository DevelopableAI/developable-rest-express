import { Router } from "express";
import auth from "../middleware/auth";
import validate from "../validators/user.validator";
import userController from "../controllers/user.controller";

const router = Router();

router.get("/users", auth, validate.listUsers, userController.listUsers);
router.post("/users", auth, validate.createUser, userController.createUser);

export default router;
