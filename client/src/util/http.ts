import axios from "axios";
import { getJWTStringOrNull } from "./localstorage";

export const axiosInstance = axios.create({
    baseURL: 'http://127.0.0.1/api/',
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