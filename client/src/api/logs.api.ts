import axios, { AxiosResponse } from "axios";
import { axiosInstance, ENV } from "../util/http";

export enum LogLevel {
    info = 'info',
    warning = 'warning',
    error = 'error',
    trace = 'trace',
    debug = 'debug',
}

export interface LogDTO {
    date_time: string,
    level: LogLevel,
    text: string,
}

export interface LogQueryInfoDTO {
    page: number,
    page_size: number,
    total_pages: number,
    total_hits: number,
}

export interface LogQueryDTO {
    hits: LogDTO[],
    info: LogQueryInfoDTO
}

export class LogsService {
    static async Search(query: string, page: number, page_size: number, sort_by: string, sort_ascending: boolean): Promise<AxiosResponse<LogQueryDTO>> {
        // TODO: Once we put the searching inside the main server, use axiosInstance and the proper endpoint.
        return await axios.get('http://127.0.0.1:8068/search_logs', {
            params: {
                query,
                page_number: page,
                page_size,
                sort_by,
                sort_ascending,
            },
        });
    }
}