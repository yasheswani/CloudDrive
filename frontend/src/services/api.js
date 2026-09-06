import axios from "axios";

const getBaseURL = () => {
    if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== "") {
        return import.meta.env.VITE_API_URL.trim().replace(/\/+$/, "");
    }

    if (typeof window !== "undefined" && window.location.hostname.endsWith("vercel.app")) {
        return "https://cloud-drive-dbpa.vercel.app";
    }

    return "http://localhost:8000";
};

export const api = axios.create({
    baseURL: getBaseURL(),
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("clouddrive_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            window.dispatchEvent(
                new Event("clouddrive:unauthorized")
            );
        }
        return Promise.reject(error);
    }
);
