const express = require("express");
const auth = require("./middleware/auth");
const healthController = require("./controllers/health.controller");

const app = express();

app.get("/health", auth, healthController.showHealth);

module.exports = app;
