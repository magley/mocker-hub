import React, { useEffect, useState } from 'react';
import { RepoExtDTO } from '../api/repo.api';
import { Card, Button, Alert } from 'react-bootstrap';
import { RepositoryService } from '../api/repo.api';
import { ToastType, useToastStore } from '../util/toastStore';
import { AxiosError } from 'axios';
import { RepositoryVisibilityUpdateDTO } from '../api/repo.api' 

export const RepoSettings: React.FC<{ isActive: boolean, repo: RepoExtDTO, repoStateChanger: any }> = (props) => {
    const addToast = useToastStore((state) => state.addToast);
    const [error, setError] = useState('');

    useEffect(() => {
        if (props.isActive) {
            // Tab selected, do stuff here...
        }
    }, [props.isActive]);

    const changeVisibility = () => {
        let dto: RepositoryVisibilityUpdateDTO = {
            public: !props.repo.public,
        };

        RepositoryService.UpdateRepoVisibilityById(props.repo.id, dto).then((res) => {
            props.repoStateChanger({
                ...props.repo,
                ...res.data,
            });
            addToast(`Updated repository ${props.repo.name}`, ToastType.success);
            setError('');
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    }

    return (
        <div className="tab-pane fade show active" id="settings">
            <Card className="mt-4">
                <Card.Body>
                    <Card.Title className="d-flex align-items-center">
                        <h5 className="mb-0">Visibility settings</h5>
                        <span className={`badge rounded-pill bg-${props.repo.public ? 'primary' : 'secondary'}`} style={{ marginLeft: '0.5em' }}>
                            <i className={`bi ${props.repo.public ? 'bi-unlock' : 'bi-lock'}`}></i>
                        </span>
                    </Card.Title>
                    {error && <Alert variant="danger">{error}</Alert>}
                    <p className="text-muted mt-3">
                        {props.repo.public ? "This repository is public." : "This repository is private."}
                    </p>
                    <Button variant="outline-primary" onClick={changeVisibility}>
                        Change visibility
                    </Button>
                </Card.Body>
            </Card>
        </div>
    );
};