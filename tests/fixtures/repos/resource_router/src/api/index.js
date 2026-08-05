import { Router } from "express";
import resources from "resource-router-middleware";
export default () => {
  const router = Router();
  router.use("/items", resources());
  return router;
};
