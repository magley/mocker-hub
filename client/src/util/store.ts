import { create } from "zustand";
import { getJwtRole } from "./localstorage";

interface AuthState {
    role: string;
    setRole: (role: string, callback?: () => void) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    role: getJwtRole(),
    setRole: (role, callback) => {
        set({ role }, false);
        if (callback) callback();
    },
}));