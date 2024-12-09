import { useEffect } from 'react';
import './UserLogin.css';
import { useNavigate } from 'react-router-dom';

export const UserLogout = () => {
    let navigate = useNavigate();
    
    useEffect(() => {
        localStorage.removeItem("token");
        
        navigate("/login", { replace: true });
    }, [navigate]);

    return null;
};
