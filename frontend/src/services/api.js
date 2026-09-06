import axios from "axios";


const API_URL =
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000";


export const api = axios.create({
    baseURL: API_URL.replace(/\/+$/, ""),
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


/*
 * If the backend says the session has expired,
 * don't leave the application in a broken state.
 *
 * The application itself handles redirecting to
 * the authentication screen.
 */
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
