import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic, OrganizationService } from "../api/org.api";
import { Spinner } from "react-bootstrap";

export const OrgSettings: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isActive) {
            setLoading(false);
        }
    }, [isActive]);

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    return (
        <>
            This is where settings go. <br />
            Desc: {org.desc} <br />
            <img src={OrganizationService.GetImageURI(org.image)} /> <br />
        </>
    );
}