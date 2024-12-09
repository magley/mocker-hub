import { AxiosResponse } from "axios";
import { axiosInstance } from "../util/http";
import { getJWTStringOrNull } from "../util/localstorage";

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

export interface UserPasswordChangeDTO {
    old_password: string,
    new_password: string,
}

export interface UserLoginDTO {
    username: string,
    password: string,
}

export interface TokenDTO {
    token: string,
}

export class UserService {
    static async RegisterRegularUser(dto: UserRegisterDTO): Promise<void> {
        return await axiosInstance.post(`/users`, dto);
    }

    static async ChangePassword(dto: UserPasswordChangeDTO): Promise<AxiosResponse<null>> {
        return await axiosInstance.post(`/users/password`, dto);
    }

    static async LoginUser(dto: UserLoginDTO): Promise<AxiosResponse<TokenDTO>> {
        return await axiosInstance.post(`/users/login`, dto);
    }
}