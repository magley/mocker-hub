import React, { useEffect } from "react";

export const OrgMembers: React.FC<{ isActive: boolean }> = ({ isActive }) => {
    useEffect(() => {
        if (isActive) { }
    }, [isActive]);

    return (
        <>
            This is where members go.
        </>
    );
}