import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Card, Row, Col, Spinner } from 'react-bootstrap';
import { RepoDTO, RepositoryService } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import './RepoOfUser.css';
import { getJwtId } from '../util/localstorage';

export const RepositoriesOfUser: React.FC = () => {
    const [repositories, setRepositories] = useState<RepoDTO[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const { userid } = useParams<{ userid: string }>();
    const [myId, setMyId] = useState<number>();

    useEffect(() => {
        fetchRepos();

        setMyId(getJwtId());
    }, []);

    const fetchRepos = () => {
        RepositoryService.GetRepositoriesOfUser(Number.parseInt(userid!)).then((res: AxiosResponse<RepoDTO[]>) => {
            setLoading(false);
            setRepositories(res.data);

            console.log(res.data);
        }).catch((err: AxiosError) => {
            setError(`${err}`);

            console.error(err);
        })
    }

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    if (error) {
        return <div className="alert alert-danger">{error}</div>;
    }

    return (
        <Row className="g-4 repo-of-user">
            {userid == myId ? (<h1>Your repositories</h1>) : (<h1>{userid}'s repositories</h1>)}

            {repositories.map((repo) => (
                <Col key={repo.id} xs={12}>
                    <Card>
                        <Card.Body>
                            {/* Repository Title with React Router Link */}
                            <Card.Title>
                                <Link to={`/repo/${repo.canonical_name}`} className="text-primary">
                                    <span>{repo.name}</span>
                                </Link>
                                {!repo.public && (
                                    <span className="badge rounded-pill bg-secondary" style={{ fontSize: '0.7rem', marginLeft: '1em' }}>
                                        <i className="bi bi-lock"></i>
                                        Private
                                    </span>
                                )}
                            </Card.Title>

                            {/* Organization Name (if exists) */}
                            {repo.organization_id && (
                                <Card.Subtitle className="mb-2 text-muted" style={{ fontSize: '0.8rem' }}>
                                    Part of organization {repo.organization_id}
                                </Card.Subtitle>
                            )}

                            {/* Description */}
                            {repo.desc && (
                                <Card.Text style={{ fontSize: '0.9rem' }}>
                                    {repo.desc}
                                </Card.Text>
                            )}

                            {/* Star Count [TODO] */}
                            {/*repo.stars > 0*/ true && (
                                <div className="d-flex align-items-center">
                                    <i className="bi bi-moon moon"></i>
                                    <span>{17}</span>
                                    {/* <span>{repo.stars}</span> */}
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            ))}
        </Row>
    );
};