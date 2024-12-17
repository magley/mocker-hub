import React, { useEffect } from 'react';
import { RepoDTO } from '../api/repo.api';

export const RepoOverview: React.FC<{ isActive: boolean, repo: RepoDTO }> = (props) => {
    useEffect(() => {
        if (props.isActive) {
            // Tab selected, do stuff here...
        }
    }, [props.isActive]);

    return (
        <div className="tab-pane fade show active" id="overview">
            <p>{props.repo.desc}</p>
        </div>
    );
};