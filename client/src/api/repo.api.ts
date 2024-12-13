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
    organization_id: number,
}


export class RepositoryService {
    static async CreateRepository(dto: RepoCreateDTO): Promise<AxiosResponse<RepoDTO>> {
        return await axiosInstance.post(`/repositories`, dto);
    }
}