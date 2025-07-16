import React, { useEffect, useState } from 'react';
import { RepoExtDTO, RepositoryService } from '../api/repo.api';
import { RepositoryDescUpdateDTO } from '../api/repo.api';
import { ToastType, useToastStore } from '../util/toastStore';
import { Alert, Card } from 'react-bootstrap';
import { AxiosError } from 'axios';
import { OrganizationDTOBasic, OrganizationService, OrgDescUpdateDTO } from '../api/org.api';
import { getJwtId } from '../util/localstorage';

export const OrgOverview: React.FC<{ isActive: boolean; org: OrganizationDTOBasic, setOrg: any }> = (props) => {
    const [isEditing, setIsEditing] = useState(false);
    const [newDesc, setNewDesc] = useState(props.org.desc);
    const addToast = useToastStore((state) => state.addToast);
    const [error, setError] = useState('');
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false);
    
    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === props.org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    }
    
    useEffect(() => {
        if (props.isActive) {
            checkIfIamOwnerOfOrg();
        }
    }, [props.isActive]);

    const updateDescription = () => {
        setIsEditing(false);

        let dto: OrgDescUpdateDTO = {
            desc: newDesc,
        };
        
        OrganizationService.UpdateOrgDescByName(props.org.name, dto).then((res) => {
            props.setOrg({
                ...props.org,
                ...res.data,
            });
            addToast(`Updated the description of ${props.org.name}.`, ToastType.success);
            setError('');
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

    return (
        <>
            {/* Consider placing the image next to the organization name */}
            <img src={OrganizationService.GetImageURI(props.org.image)} /> <br /> 

            <div className="tab-pane fade show active" id="overview">
                {error && <Alert variant="danger">{error}</Alert>}
                {isEditing ? (
                    <div>
                        <textarea className="form-control" rows={7} value={newDesc} onChange={(e) => setNewDesc(e.target.value)} autoFocus/>
                        <div className='mt-3'>
                            <button className="btn btn-primary me-2" onClick={updateDescription}> 
                                Update description
                            </button>
                            <button className="btn btn-secondary" onClick={() => { setIsEditing(false); setNewDesc(props.org.desc); }}> 
                                Cancel 
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="d-flex align-items-center">
                        <div className='repo-page-desc'>{props.org.desc}</div>
                        {amOwnerOfOrg && (
                            <button className="btn btn-link p-0 ms-2" onClick={() => setIsEditing(true)}>
                                <i className="bi bi-pencil"></i>
                            </button>
                        )}
                    </div>
                )}
            </div>
        </>
    );
};