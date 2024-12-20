import { create } from "zustand";

export enum ToastType {
    success = 'success',
    info = 'info',
    error = 'error',
}

interface Toast {
    id: number;
    message: string;
    type: ToastType;
    duration_ms: number;
}

interface ToastStore {
    toasts: Toast[];
    addToast: (message: string, type: ToastType, duration_ms?: number) => void;
    removeToast: (id: number) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
    toasts: [],
    addToast: (message, type, duration_ms = 5000) => {
        const id = Date.now();
        set((state) => ({
            toasts: [...state.toasts, { id, message, type, duration_ms }],
        }));

        // Remove the toast after 5 seconds
        setTimeout(() => {
            set((state) => ({
                toasts: state.toasts.filter((toast) => toast.id !== id),
            }));
        }, duration_ms);
    },
    removeToast: (id) => {
        set((state) => ({
            toasts: state.toasts.filter((toast) => toast.id !== id),
        }));
    },
}));
