import userRepository from "../repositories/user.repository";

const listUsers = async () => userRepository.listUsers();
const createUser = async () => userRepository.createUser();

export default { listUsers, createUser };
