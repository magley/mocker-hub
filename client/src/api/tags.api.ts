import { AxiosResponse } from "axios";
import { axiosInstance } from "../util/http";
import { PaginationDTO, PaginationParams } from "../util/pagination";

export interface TagDTO {
    id: number,
    name: string | null,
    last_push: string, // Encoded Date() object.
    last_pushed_by_username: string,
}

export interface DeleteTagDTO {
    repo_id: number,
    tag_name: string
}

export interface DeleteTagResponseDTO {
    message: string
}

export class TagsService {
    static async GetAllTagsOfRepo(repo_canonical_name: string): Promise<AxiosResponse<TagDTO[]>> {
        return await axiosInstance.get(`/tags/?repo_name=${repo_canonical_name}`);
    }

    static async FilterTagsOfRepo(repo_canonical_name: string, search_query: string, pagination: PaginationParams): Promise<AxiosResponse<PaginationDTO<TagDTO>>> {
        const queryParams = pagination.toQueryParams();
        queryParams.append('repo_name', repo_canonical_name);
        queryParams.append('search_query', search_query);

        return await axiosInstance.get(`/tags/filter?${queryParams.toString()}`);
    }


    static async DeleteTag(dto: DeleteTagDTO): Promise<AxiosResponse<DeleteTagResponseDTO>> {
        return await axiosInstance.delete(`/registry/tag`, { data: dto });
    }
}