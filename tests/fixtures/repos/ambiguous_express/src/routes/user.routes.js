const express = require("express");
const userService = require("../services/user.service");

const router = express.Router();
router.get("/users", userService.listUsers);

module.exports = router;
