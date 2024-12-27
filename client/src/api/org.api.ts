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

export interface OrganizationHasMemberDTO {
    org_id: number
    user_id: number | null
    is_member: boolean
}

export class OrganizationService {
    static async CreateOrganization(dto: OrganizationCreateDTO): Promise<AxiosResponse<OrganizationDTOBasic>> {
        return await axiosInstance.post(`/organizations`, dto);
    }

    static async GetMyOrganizations(): Promise<AxiosResponse<OrganizationDTOBasic[]>> {
        return await axiosInstance.get(`/organizations/my`);
    }

    static async FindByName(name: string): Promise<AxiosResponse<OrganizationDTOBasic>> {
        return await axiosInstance.get(`/organizations/name/${name}`);
    }

    static GetImageURI = (filename: string): string => {
        return `${ENV.IMG}${filename}`;
    }
        
    static async AmIMemberOfOrg(org_id: number): Promise<AxiosResponse<OrganizationHasMemberDTO>> {
        return await axiosInstance.get(`/organizations/me/${org_id}`);
    }
}