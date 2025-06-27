import React, { useEffect, useState } from 'react';
import { RepoExtDTO } from '../api/repo.api';
import { Card, Button, Alert } from 'react-bootstrap';
import { RepositoryService } from '../api/repo.api';
import { ToastType, useToastStore } from '../util/toastStore';
import { AxiosError } from 'axios';
import { RepositoryVisibilityUpdateDTO } from '../api/repo.api' 

export const RepoSettings: React.FC<{ isActive: boolean, repo: RepoExtDTO, setRepo: any }> = (props) => {
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
            props.setRepo({
                ...props.repo,
                ...res.data,
            });
            if (res.data.public) {
                addToast(`${props.repo.name} is now a public repository.`, ToastType.success);
            } else {
                addToast(`${props.repo.name} is now a private repository.`, ToastType.success);
            }
            setError('');
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    }

    const handleDeleteRepo = async () => {
            RepositoryService.DeleteRepo(props.repo.id)
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
                        {props.repo.public ? <> This repository is <strong>public</strong>.</> : <> This repository is <strong>private</strong>.</> }
                    </p>
                    <Button variant="outline-primary" onClick={changeVisibility}>
                        {props.repo.public ? 'Make private' : 'Make public'}
                    </Button>
                </Card.Body>
            </Card>
        
            <Card className="mt-4">
                <Card.Body>
                    <Card.Title className="d-flex align-items-center">
                        <h5 className="mb-0">Delete repository</h5>
                    </Card.Title>
                    {error && <Alert variant="danger">{error}</Alert>}
                    <p className="text-muted mt-3"> Deleting a repository will destroy all images stored within it. This action cannot be undone. </p>
                    <Button variant="outline-danger" onClick={handleDeleteRepo}>Delete repository</Button>
                </Card.Body>
            </Card>
        </div>
    );
};