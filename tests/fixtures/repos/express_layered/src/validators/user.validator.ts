import Joi from "joi";

const createUser = Joi.object({ name: Joi.string().required() });
const listUsers = Joi.object({});

export default { createUser, listUsers };
