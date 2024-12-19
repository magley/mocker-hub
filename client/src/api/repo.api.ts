import { AxiosResponse } from "axios";
import { axiosInstance } from "../util/http";

export enum RepositoryBadge {
    none = "none",
    official = "official",
    verified = "verified",
    sponsored_oss = "sponsored_oss",
}

export interface RepoCreateDTO {
    name: string,
    desc: string,
    public: boolean,
    organization_id: number | null,
}

export interface RepoDTO {
    id: number,
    name: string,
    canonical_name: string,
    desc: string
    public: boolean,
    owner_id: number,
    organization_id: number | null,
    badge: RepositoryBadge,
    last_updated: string, // Encoded Date() object.
    downloads: number,
}

export interface ReposOfUserDTO {
    user_id: number,
    user_name: string,
    repos: RepoDTO[],
    organization_names: { [key: number]: string };
}

export interface RepoExtDTO extends RepoDTO {
    owner_name: string,
    org_name: string | null,
}

export class RepositoryService {
    static BadgeToHumanText(badge: RepositoryBadge): string {
        switch (badge) {
            case RepositoryBadge.none: return "";
            case RepositoryBadge.official: return "Official";
            case RepositoryBadge.verified: return "Verified Publisher";
            case RepositoryBadge.sponsored_oss: return "Sponsored OSS";
            default: return `${badge}`;
        }
    }

    static BadgeToBootstrapColor(badge: RepositoryBadge): string {
        switch (badge) {
            case RepositoryBadge.none: return "bg-light";
            case RepositoryBadge.official: return "bg-primary";
            case RepositoryBadge.verified: return "bg-secondary";
            case RepositoryBadge.sponsored_oss: return "bg-success";
            default: return `bg-light`;
        }
    }

    /**
     * 
     * Usage: <i className={`bi ${BadgeToBootstrapIcon(...)}`}></i>
     */
    static BadgeToHumanBootstrapIcon(badge: RepositoryBadge): string {
        switch (badge) {
            case RepositoryBadge.none: return "";
            case RepositoryBadge.official: return "bi-award";
            case RepositoryBadge.verified: return "bi-patch-check-fill";
            case RepositoryBadge.sponsored_oss: return "bi-git";
            default: return ``;
        }
    }

    static async CreateRepository(dto: RepoCreateDTO): Promise<AxiosResponse<RepoDTO>> {
        return await axiosInstance.post(`/repositories`, dto);
    }

    static async GetRepositoriesOfUser(username: string): Promise<AxiosResponse<ReposOfUserDTO>> {
        return await axiosInstance.get(`/repositories/u/${username}`);
    }


    static async GetRepoByCanonicalName(name: string): Promise<AxiosResponse<RepoExtDTO>> {
        return await axiosInstance.get(`/repositories/${name}`);
    }
}