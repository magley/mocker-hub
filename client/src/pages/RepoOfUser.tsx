import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Card, Row, Col, Spinner, Button } from 'react-bootstrap';
import { RepoDTO, RepositoryService, ReposOfUserDTO } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import './RepoOfUser.css';
import { getJwtId } from '../util/localstorage';

export const RepositoriesOfUser: React.FC = () => {
    const [fullResult, setFullResult] = useState<ReposOfUserDTO>();
    const [orgNames, setOrgNames] = useState<Map<number, string>>();
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const { userid } = useParams<{ userid: string }>();
    const [myId, setMyId] = useState<number>();

    const [repositories, setRepositories] = useState<RepoDTO[]>([]);
    const [filteredRepos, setFilteredRepos] = useState<RepoDTO[]>([]);

    const [searchTerm, setSearchTerm] = useState('');
    const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
    const [selectedOrg, setSelectedOrg] = useState<number | undefined>(undefined);
    const [showPublic, setShowPublic] = useState(true);
    const [showPrivate, setShowPrivate] = useState(true);

    useEffect(() => {
        fetchRepos();

        setMyId(getJwtId());
    }, []);

    const fetchRepos = () => {
        RepositoryService.GetRepositoriesOfUser(Number.parseInt(userid!)).then((res: AxiosResponse<ReposOfUserDTO>) => {
            setLoading(false);
            setFullResult(res.data);
            setRepositories(res.data.repos);

            const orgNamesMap = new Map(Object.entries(res.data.organization_names).map(([key, value]) => [Number(key), value]));
            setOrgNames(orgNamesMap);

            setRepositories(res.data.repos);
            setFilteredRepos(res.data.repos);
        }).catch((err: AxiosError) => {
            setError(`${err}`);
        })
    }

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        filterRepos(e.target.value, selectedOrg, showPublic, showPrivate);
    };

    const toggleAdvancedSearch = () => {
        setShowAdvancedSearch(!showAdvancedSearch);
    };

    const handleOrgChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const orgId = Number(e.target.value);
        setSelectedOrg(orgId);
        filterRepos(searchTerm, orgId, showPublic, showPrivate);
    };

    const handlePublicChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowPublic(e.target.checked);
        filterRepos(searchTerm, selectedOrg, e.target.checked, showPrivate);
    };

    const handlePrivateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowPrivate(e.target.checked);
        filterRepos(searchTerm, selectedOrg, showPublic, e.target.checked);
    };

    const filterRepos = (searchTerm: string, orgId?: number, showPublic?: boolean, showPrivate?: boolean) => {
        let filtered = repositories.filter((repo) => {
            const matchesSearch =
                repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (repo.desc && repo.desc.toLowerCase().includes(searchTerm.toLowerCase()));
            const matchesOrg = orgId ? repo.organization_id === orgId : true;
            const matchesVisibility = (showPublic && repo.public) || (showPrivate && !repo.public);
            return matchesSearch && matchesOrg && matchesVisibility;
        });
        setFilteredRepos(filtered);
    };


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
            {/* Page Title */}
            {userid == myId ? (<h1>Your repositories</h1>) : (<h1>{fullResult!.user_name}'s repositories</h1>)}

            <div className="d-flex justify-content-between">
                {/* Search Bar */}
                <input
                    type="text"
                    className="form-control me-2"
                    placeholder="Search repositories"
                    value={searchTerm}
                    onChange={handleSearchChange}
                />
                {/* Advanced Search Button */}
                <Button className="btn btn-primary" onClick={toggleAdvancedSearch}>
                    {showAdvancedSearch ? <i className="bi bi-funnel-fill"></i> : <i className="bi bi-funnel"></i>}
                </Button>
            </div>

            {/* Advanced Search Section */}
            {showAdvancedSearch && (
                <div className="advanced-search">
                    <div className="mb-1">
                        <select
                            id="orgSelect"
                            className="form-select"
                            value={selectedOrg || ''}
                            onChange={handleOrgChange}
                        >
                            <option value="">All Organizations</option>
                            {Array.from(orgNames!.entries()).map(([id, name]) => (
                                <option key={id} value={id}>
                                    {name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Visibility Filter - Public/Private Checkboxes */}
                    <div className="mb-3">
                        <div className="form-check ms-2 d-flex align-items-center">
                            <input
                                type="checkbox"
                                className="form-check-input form-check-lg"
                                checked={showPublic}
                                onChange={handlePublicChange}
                                id="publicCheckbox"
                            />
                            <label className="form-check-label fs-5 ms-2" htmlFor="publicCheckbox">
                                <i className="bi bi-journal-bookmark"></i> <b>Public</b>
                            </label>
                        </div>
                        <div className="form-check ms-2 d-flex align-items-center">
                            <input
                                type="checkbox"
                                className="form-check-input form-check-lg"
                                checked={showPrivate}
                                onChange={handlePrivateChange}
                                id="privateCheckbox"
                            />
                            <label className="form-check-label fs-5 ms-2" htmlFor="privateCheckbox">
                                <i className="bi bi-lock"></i> <b>Private</b>
                            </label>
                        </div>
                    </div>
                </div>
            )}

            {filteredRepos.map((repo) => (
                <Col key={repo.id} xs={12}>
                    <Card>
                        <Card.Body>
                            {/* Repository Title with React Router Link */}
                            <Card.Title>
                                <Link to={`/r/${repo.canonical_name}`} className="text-primary">
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
                                    Part of organization {orgNames?.get(repo.organization_id)}
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