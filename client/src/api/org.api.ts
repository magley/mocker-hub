import { AxiosResponse } from "axios";
import { axiosInstance, ENV } from "../util/http";

export interface OrganizationCreateDTO {
    name: string
    desc: string
    image: string | null
}

export interface OrganizationDTOBasic {
    id: number
    name: string
    desc: string
    image: string
    owner_id: number
}

export interface OrganizationRepoDTO {
    id: number
    name: string
    canonical_name: string
    desc: string
}

export interface OrganizationDTO extends OrganizationDTOBasic {
    repositories: OrganizationRepoDTO[]
}

export class OrganizationService {
    static async CreateOrganization(dto: OrganizationCreateDTO): Promise<AxiosResponse<OrganizationDTOBasic>> {
        return await axiosInstance.post(`/organizations`, dto);
    }

    static async GetMyOrganizations(): Promise<AxiosResponse<OrganizationDTOBasic[]>> {
        return await axiosInstance.get(`/organizations/my`);
    }

    static async FindByName(name: string): Promise<AxiosResponse<OrganizationDTOBasic>> {
        return await axiosInstance.get(`/organizations/${name}`);
    }

    static GetImageURI = (filename: string): string => {
        return `${ENV.IMG}${filename}`;
    }
}