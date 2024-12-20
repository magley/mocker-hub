import axios from "axios";
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