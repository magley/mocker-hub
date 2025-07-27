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
        return await axiosInstance.get("/events/", {
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