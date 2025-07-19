import axios from "axios";
import { AxiosError } from 'axios';
import { getJWTStringOrNull } from "./localstorage";

export const ENV = {
    API: 'http://127.0.0.1/api/',
    IMG: 'http://localhost/img/',
};

export const axiosInstance = axios.create({
    baseURL: ENV.API,
});

axiosInstance.interceptors.request.use(
    (config) => {
        const token = getJWTStringOrNull();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        console.error(error);
    }
);

/**
 * Given an error received from the API (notably, the server), create a
 * human-readable string that can be shown on the web app. 
 * @throws Never
 * @param err Axios error
 * @returns A human-readable string that can be shown on the web app
 */
export const get_validation_error_readable = (err: AxiosError): string => {
    try {
        let err_msg = (err.response?.data as any)["detail"]["message"];
        if (Array.isArray(err_msg)) {
            return err_msg[0]["msg"];
        } else if (typeof err_msg == "string") {
            return err_msg;
        } else {
            return (err.response?.data as any)["detail"]["message"];
        }
    } catch (e) {
        console.error(e);
        console.error(err.response?.data as any);
        return "Invalid user input";
    }
}