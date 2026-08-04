import { userController } from "../../controllers/user.controller";
router.get("/users", userController.list);
