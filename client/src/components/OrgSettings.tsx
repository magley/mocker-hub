import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic, OrganizationService } from "../api/org.api";
import { Button, Card, Spinner } from "react-bootstrap";
import { AxiosError } from "axios";
import { ToastType, useToastStore } from "../util/toastStore";
import { getJwtId } from "../util/localstorage";

export const OrgSettings: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
    const [loading, setLoading] = useState(true);
    const addToast = useToastStore((state) => state.addToast);
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false);
    
    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    }

    useEffect(() => {
        if (isActive) {
            setLoading(false);
            checkIfIamOwnerOfOrg();
        }
    }, [isActive]);

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    const handleDeleteOrg = async () => {
        OrganizationService.DeleteOrg(org.name)
            .then((res) => {
                addToast(res.data.message, ToastType.success);
            })
            .catch((err: AxiosError) => {
                const data = (err.response?.data ?? {}) as any;
                const msg = typeof data.detail === 'string' ? data.detail : data.detail?.message;
                addToast(msg, ToastType.error);
            })
    };
    
    return (
        <>
            <Card className="mt-4">
                <Card.Body>
                    <img src={OrganizationService.GetImageURI(org.image)} /> <br />
                    Desc: {org.desc} <br />
                </Card.Body>
            </Card>

            {amOwnerOfOrg && 
                <Card className="mt-4">
                    <Card.Body>
                        <Card.Title className="d-flex align-items-center">
                            <h5 className="mb-0">Delete organization</h5>
                        </Card.Title>
                        <p className="text-muted mt-3"> Deleting an organization will destroy all information (repositories, images, members, ...) stored within it. This action cannot be undone. </p>
                        <Button variant="outline-danger" onClick={handleDeleteOrg}>Delete organization</Button>
                    </Card.Body>
                </Card>
            }
        </>
    );
}