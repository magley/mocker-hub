import { useEffect } from 'react';
import './UserLogin.css';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../util/store';

export const UserLogout = () => {
    let navigate = useNavigate();
    const setRole = useAuthStore((state) => state.setRole);

    useEffect(() => {
        localStorage.removeItem("jwt");
        setRole("");
        navigate("/login", { replace: true });
    }, [navigate]);

    return null;
};
