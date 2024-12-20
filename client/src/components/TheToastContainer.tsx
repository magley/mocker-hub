import { Toast, ToastContainer as BootstrapToastContainer } from 'react-bootstrap';
import { ToastType, useToastStore } from '../util/toastStore';

export const TheToastContainer = () => {
    const toasts = useToastStore((state) => state.toasts);
    const removeToast = useToastStore((state) => state.removeToast);

    const getToastIcon = (type: ToastType) => {
        switch (type) {
            case ToastType.success: return "bi bi-check-circle";
            case ToastType.info: return "bi bi-info-circle";
            case ToastType.error: return "bi bi-dash-circle";
        }
        return "bi bi-info-circle";
    }

    return (
        <BootstrapToastContainer position="top-end" className="p-3">
            {toasts.map((toast, i) => (
                <Toast
                    key={`${toast.id}_${i}`}
                    bg={toast.type}
                    delay={toast.duration_ms}
                    autohide
                    onClose={() => removeToast(toast.id)}
                >
                    <Toast.Body>
                        <i className={getToastIcon(toast.type)}> </i>
                        {toast.message}
                    </Toast.Body>
                </Toast>
            ))}
        </BootstrapToastContainer>
    );
};