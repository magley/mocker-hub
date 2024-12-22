import { AxiosResponse } from "axios";
import { axiosInstance, ENV } from "../util/http";

export enum TeamPermissionKind {
    read = "read",
    read_write = "read_write",
    admin = "admin"
}

export interface TeamDTOMember {
    id: number;
    username: string;
}

export interface TeamPermissionsDTO {
    team_id: number;
    repo_id: number;
    kind: TeamPermissionKind;
}

export interface TeamDTOBasic {
    id: number;
    name: string;
    organization_id?: number | null;
}

export interface TeamDTOFull extends TeamDTOBasic {
    members: TeamDTOMember[];
    permissions: TeamPermissionsDTO[];
}

export interface TeamCreateDTO {
    name: string;
    organization_id: number;
}

export interface TeamAddMemberDTO {
    team_id: number;
    user_id: number;
}

export interface TeamAddPermissionDTO extends TeamPermissionsDTO {}

export class TeamService {
    static async FindByOrganizationId(org_id: number): Promise<AxiosResponse<TeamDTOBasic[]>> {
        return await axiosInstance.get(`/teams/o/${org_id}`);
    }

    static async Create(dto: TeamCreateDTO): Promise<AxiosResponse<TeamDTOBasic>> {
        return await axiosInstance.post(`/teams`, dto);
    }
}