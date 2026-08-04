import userService from "../services/user.service";

const listUsers = async (_req: unknown, res: { json: (value: unknown) => void }) => {
  res.json(await userService.listUsers());
};

const createUser = async (_req: unknown, res: { json: (value: unknown) => void }) => {
  res.json(await userService.createUser());
};

export default { listUsers, createUser };
