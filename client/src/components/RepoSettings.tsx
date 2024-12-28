import React, { useEffect } from 'react';
import { RepoExtDTO } from '../api/repo.api';
import { Card, Button } from 'react-bootstrap';

export const RepoSettings: React.FC<{ isActive: boolean, repo: RepoExtDTO }> = (props) => {
    useEffect(() => {
        if (props.isActive) {
            // Tab selected, do stuff here...
        }
    }, [props.isActive]);

    return (
        <div className="tab-pane fade show active" id="settings">
            <Card className="mt-4">
                <Card.Body>
                    <Card.Title className="d-flex align-items-center">
                        <h5 className="mb-0">Visibility settings</h5>
                        <span
                            className={`badge rounded-pill bg-${
                                props.repo.public ? 'primary' : 'secondary'
                            }`}
                            style={{ marginLeft: '0.5em' }}
                        >
                            <i
                                className={`bi ${
                                    props.repo.public ? 'bi-unlock' : 'bi-lock'
                                }`}
                            ></i>
                        </span>
                    </Card.Title>
                    <p className="text-muted mt-3">
                        {props.repo.public
                            ? "This repository is public."
                            : "This repository is private."}
                    </p>
                    <Button variant={`outline-${
                                props.repo.public ? 'secondary' : 'primary'
                            }`} >
                        {props.repo.public ? 'Make private' : 'Make public'}
                    </Button>
                </Card.Body>
            </Card>
        </div>
    );



    
};