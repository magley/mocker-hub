import React, { useEffect, useState } from 'react';
import { RepoExtDTO } from '../api/repo.api';

export const RepoOverview: React.FC<{ isActive: boolean; repo: RepoExtDTO }> = (props) => {
    const [isEditing, setIsEditing] = useState(false);
    const [newDesc, setNewDesc] = useState(props.repo.desc);

    useEffect(() => {
        if (props.isActive) {
            // Tab selected, do stuff here...
        }
    }, [props.isActive]);

    const updateChanges = () => {
        console.log("Saving:", newDesc);
        setIsEditing(false);
    };

    return (
        <div className="tab-pane fade show active" id="overview">
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
                    <p className="mb-0">{props.repo.desc}</p>
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