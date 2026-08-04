import { User } from "../models/user.model";
export const userService = { list: () => User.find() };
