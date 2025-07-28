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

export enum UserBadge {
    none = "none",
    verified = "verified",
    sponsored_oss = "sponsored_oss",
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
    badge: UserBadge,
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

export interface UserQueryInfoDTO {
    page: number,
    page_size: number,
    total_pages: number,
    total_hits: number,
}

export interface UserQueryDTO {
    hits: UserDTO[],
    info: UserQueryInfoDTO
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

    static async SearchUsersPaginated(query: string, page: number, page_size: number, sort_by: string, sort_ascending: boolean): Promise<AxiosResponse<UserQueryDTO>> {
        return await axiosInstance.get(`/users/paginated/`, {
            params: {
                page_number: page,
                page_size,
                sort_by,
                sort_ascending,
                query
            }
        });
    }

    
     static BadgeToHumanText(badge: UserBadge): string {
            switch (badge) {
                case UserBadge.none: return "";
                case UserBadge.verified: return "Verified Publisher";
                case UserBadge.sponsored_oss: return "Sponsored OSS";
                default: return `${badge}`;
            }
        }

    static BadgeToBootstrapColor(badge: UserBadge): string {
            switch (badge) {
                case UserBadge.none: return "bg-light";
                case UserBadge.verified: return "bg-secondary";
                case UserBadge.sponsored_oss: return "bg-success";
                default: return `bg-light`;
            }
        }

        static BadgeToHumanBootstrapIcon(badge: UserBadge): string {
            switch (badge) {
                case UserBadge.none: return "";
                case UserBadge.verified: return "bi-patch-check-fill";
                case UserBadge.sponsored_oss: return "bi-git";
                default: return ``;
            }
        }
}