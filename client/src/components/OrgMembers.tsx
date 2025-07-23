import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic, OrganizationService } from "../api/org.api";
import { UserDTO } from "../api/user.api";
import { AxiosError, AxiosResponse } from "axios";
import { Button, Spinner } from "react-bootstrap";
import { getJwtId } from "../util/localstorage";

export const OrgMembers: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
    const [members, setMembers] = useState<UserDTO[]>([]);
    const [loading, setLoading] = useState(true);
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false);

    const [showModal, setShowModal] = useState(false);

    useEffect(() => {
        if (isActive) { 
            getMembers();
            checkIfIamOwnerOfOrg();
        }
    }, [isActive]);

    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    }

    const getMembers = () => {
        setLoading(true);
        setMembers([]);

        OrganizationService.GetMembersOfOrg(org.id).then((res: AxiosResponse<UserDTO[]>) => {
            setMembers(res.data);
        }).catch((err: AxiosError) => {
            console.error(err);
        }).finally(() => {
            setLoading(false);
        })
    }

    const handleShow = () => setShowModal(true);

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    return (
        <>
            {/* No members */}

            {members.length == 0 && (<>
                <h1 className="no-teams-text">This organization does not have any members.</h1>
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-center">
                        <Button variant="primary" onClick={handleShow}>Add Member</Button>
                    </div>
                )}
            </>)}

            {/* Yes members */}
            {members.length > 0 && (<>
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-center">
                        <Button variant="primary" onClick={handleShow}>Add Member</Button>
                    </div>
                )}

                {members.length > 0 && (members.map((member, i) => (
                    <div key={i}>{member.username} (TODO - View add and remove members)</div>
                )))}
            </>)}
        </>
    );
}