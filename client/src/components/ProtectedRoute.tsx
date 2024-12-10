import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../util/store';

interface ProtectedRouteProps {
    children: React.ReactNode;
    requiredRole?: string | string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
    const role = useAuthStore((state) => state.role);

    if (requiredRole) {
        const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
        const hasRequiredRole = roles.length == 0 || roles.includes(role);

        if (!hasRequiredRole) {
            if (!role) {
                console.error("Please sign in");
                return <Navigate to="/login" />;
            }

            console.error(`You are unauthorized to access this route. Allowed roles: ${requiredRole}. Your role: ${role}.`);
            return <Navigate to="/" />;
        }
    }

    return children;
};