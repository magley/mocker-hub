import React, { useEffect, useState } from 'react';
import { RepoExtDTO, RepositoryService } from '../api/repo.api';
import { RepositoryDescUpdateDTO } from '../api/repo.api';
import { ToastType, useToastStore } from '../util/toastStore';
import { Alert } from 'react-bootstrap';
import { AxiosError } from 'axios';

export const RepoOverview: React.FC<{ isActive: boolean; repo: RepoExtDTO, setRepo: any }> = (props) => {
    const [isEditing, setIsEditing] = useState(false);
    const [newDesc, setNewDesc] = useState(props.repo.desc);
    const addToast = useToastStore((state) => state.addToast);
    const [error, setError] = useState('');

    useEffect(() => {
        if (props.isActive) {
            // Tab selected, do stuff here...
        }
    }, [props.isActive]);

    const updateChanges = () => {
        setIsEditing(false);

        let dto: RepositoryDescUpdateDTO = {
            desc: newDesc,
        };
        
        RepositoryService.UpdateRepoDescById(props.repo.id, dto).then((res) => {
            props.setRepo({
                ...props.repo,
                ...res.data,
            });
            addToast(`Updated the description of ${props.repo.name}.`, ToastType.success);
            setError('');
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

    return (
        <div className="tab-pane fade show active" id="overview">
            {error && <Alert variant="danger">{error}</Alert>}
            {isEditing ? (
                <div>
                    <textarea className="form-control" rows={7} value={newDesc} onChange={(e) => setNewDesc(e.target.value)}/>
                    <div className='mt-3'>
                        <button className="btn btn-primary me-2" onClick={updateChanges}> 
                            Update 
                        </button>
                        <button className="btn btn-secondary" onClick={() => { setIsEditing(false); setNewDesc(props.repo.desc); }}> 
                            Cancel 
                        </button>
                    </div>
                </div>
            ) : (
                <div className="d-flex align-items-center">
                    <div className='repo-page-desc'>{props.repo.desc}</div>
                    {props.repo.can_update && (
                        <button className="btn btn-link p-0 ms-2" onClick={() => setIsEditing(true)}>
                            <i className="bi bi-pencil"></i>
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};