import { AxiosResponse } from "axios";
import { axiosInstance, ENV } from "../util/http";
import { UserDTO } from "./user.api";

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

export interface DeleteOrgResponseDTO {
    message: string
}

export interface OrgDescUpdateDTO {
    desc: string
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

    static async DeleteOrg(orgName: string) : Promise<AxiosResponse<DeleteOrgResponseDTO>> {
        return await axiosInstance.delete(`/registry/organization/${orgName}`)
    }

    static async UpdateOrgDescByName(orgName: string, dto: OrgDescUpdateDTO) : Promise<AxiosResponse<OrganizationDTOBasic>> {
        return await axiosInstance.put(`/organizations/${orgName}/desc`, dto)
    }

    static async GetMembersOfOrg(org_id: number): Promise<AxiosResponse<UserDTO[]>> {
        return await axiosInstance.get(`/organizations/${org_id}/members`);
    }

    static async AddUsersToOrg(org_id: number, user_ids: number[]) {
        return await axiosInstance.post(`/organizations/${org_id}/addMember`, user_ids);
    }
 
    static async SearchMembers(query: string, team_id_to_exclude_members: number): Promise<AxiosResponse<UserDTO[]>> {
        return await axiosInstance.get(`/organizations/search/${query}`, {
            params: {team_id_to_exclude_members}
        });
    }

}

