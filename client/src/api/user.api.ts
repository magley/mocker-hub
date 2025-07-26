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
    join_date: Date,
    first_name: string | null,
    last_name: string | null,
    bio: string | null,
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

    static async RegisterAdmin(dto: UserRegisterDTO): Promise<void> {
        return await axiosInstance.post(`/users/register-admin`, dto);
    }

    static async SearchUsers(query: string, org_id_to_exclude_members: number=0): Promise<AxiosResponse<UserDTO[]>> {
        return await axiosInstance.get(`/users/search/${query}`, {
            params: {org_id_to_exclude_members}
        });
    }

    static async GetUserProfile(username: string): Promise<AxiosResponse<UserDTO>> {
        return await axiosInstance.get(`/users/${username}`);
    }

    static async UpdateMyProfile(dto: UserDTO): Promise<AxiosResponse<UserDTO>> {
        return await axiosInstance.put(`/users`, dto);
    }
}