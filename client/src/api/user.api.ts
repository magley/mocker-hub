import { AxiosResponse } from "axios";
import { axiosInstance } from "../util/http";

export interface UserRegisterDTO {
    email: string,
    username: string,
    password: string,
}

export enum UserRole {
    user = "user",
    admin = "admin",
    superadmin = "superadmin",
}

export interface UserDTO {
    id: number,
    email: string,
    username: string,
    role: UserRole,
    join_date: Date
}

export class UserService {
    static async RegisterRegularUser(dto: UserRegisterDTO): Promise<AxiosResponse<UserDTO>> {
        return await axiosInstance.post(`/users`, dto);
    }
}