import React, { useEffect } from "react";

export const OrgTeams: React.FC<{ isActive: boolean }> = ({ isActive }) => {
    useEffect(() => {
        if (isActive) { }
    }, [isActive]);

    return (
        <>
            This is where teams go.
        </>
    );
}