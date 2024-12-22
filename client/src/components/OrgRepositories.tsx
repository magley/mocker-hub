import React, { useEffect } from "react";

export const OrgRepositories: React.FC<{ isActive: boolean }> = ({ isActive }) => {
    useEffect(() => {
        if (isActive) { }
    }, [isActive]);

    return (
        <>
            This is where repositories go.
        </>
    );
}