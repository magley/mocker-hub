import { create } from "zustand";
import { getJwtRole } from "./localstorage";

interface AuthState {
    role: string;
    setRole: (role: string) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    role: getJwtRole(),
    setRole: (val: string) => set({ role: val }),
}));
