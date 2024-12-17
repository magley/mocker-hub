import { AxiosResponse } from "axios";
import { axiosInstance } from "../util/http";

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
    official: boolean,
    owner_id: number,
    organization_id: number | null,
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
    static async CreateRepository(dto: RepoCreateDTO): Promise<AxiosResponse<RepoDTO>> {
        return await axiosInstance.post(`/repositories`, dto);
    }

    static async GetRepositoriesOfUser(user_id: number): Promise<AxiosResponse<ReposOfUserDTO>> {
        return await axiosInstance.get(`/repositories/u/${user_id}`);
    }

    static async GetRepoByCanonicalName(name: string): Promise<AxiosResponse<RepoExtDTO>> {
        return await axiosInstance.get(`/repositories/${name}`);
    }
}