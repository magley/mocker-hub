import React, { useEffect, useState } from 'react';
import { Nav, Spinner, Tab } from 'react-bootstrap';
import { RepoOverview } from '../components/RepoOverview';
import { RepoTags } from '../components/RepoTags';
import { NavLink, useNavigate, useParams } from 'react-router-dom';
import { RepoExtDTO, RepositoryService } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import "./RepoPage.css";

interface RepoOwner {
    name: string,
    id: number,
    isUser: boolean,
    official: boolean,
    linkURL: string
}

export const RepositoryPage: React.FC = () => {
    const { "*": repoName } = useParams();
    const [repo, setRepo] = useState<RepoExtDTO>();
    const [key, setKey] = useState<string>('overview');
    const [loading, setLoading] = useState<boolean>(true);
    let navigate = useNavigate();
    const [repoOwner, setRepoOwner] = useState<RepoOwner>({
        name: '...',
        id: 1,
        isUser: true,
        official: false,
        linkURL: "."
    });

    useEffect(() => {
        RepositoryService.GetRepoByCanonicalName(repoName!).then((res: AxiosResponse<RepoExtDTO>) => {
            setLoading(false);
            setRepo(res.data);
            setRepoOwner({
                name: res.data.org_name === null ? res.data.owner_name : res.data.org_name,
                id: res.data.organization_id === null ? res.data.owner_id : res.data.organization_id,
                isUser: res.data.organization_id === null,
                official: res.data.official,
                linkURL: res.data.org_name === null ? `/u/${res.data.owner_name}/repos` : `/o/${res.data.org_name}`
            });
        }).catch((err: AxiosError) => {
            if (err.response?.status == 404) {
                navigate("/");
                console.error("Not found - either a typo or access denied.");
            } else {
                console.error(err);
            }
        });
    }, []);

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    return (
        <div className="repo-page">
            {/* Repository Section */}
            <div className="repo-page-header mb-4">
                <h1>
                    {repo?.canonical_name}
                    {/* Official badge */}
                    {repo?.official &&
                        <span className="badge rounded-pill bg-primary" style={{ fontSize: '0.5em', marginLeft: '1em' }}>
                            <i className="bi bi bi-award-fill"></i>
                            Official
                        </span>
                    }
                    {/* Private badge */}
                    {!repo?.public &&
                        <span className="badge rounded-pill bg-secondary" style={{ fontSize: '0.5em', marginLeft: '0.5em' }}>
                            <i className="bi bi-lock"></i>
                            Private
                        </span>
                    }
                </h1>
                <h5>
                    {repoOwner.isUser ? <>By </> : <>Part of </>}
                    <NavLink to={repoOwner.linkURL}>{repoOwner.name}</NavLink>
                </h5>
                {/* TODO: Star count */}
                <p>
                    <i className="bi bi-moon moon"></i><span>{44}</span>
                </p>
            </div>

            {/* Tabs Section */}
            <Tab.Container activeKey={key} onSelect={(k) => setKey(k!)} id="tabs">
                <Nav variant="tabs" className="mb-3">
                    <Nav.Item>
                        <Nav.Link eventKey="overview" className={key === 'overview' ? 'active' : ''}>
                            Overview
                        </Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                        <Nav.Link eventKey="tags" className={key === 'tags' ? 'active' : ''}>
                            Tags
                        </Nav.Link>
                    </Nav.Item>
                </Nav>

                <Tab.Content>
                    <Tab.Pane eventKey="overview">
                        {repo && <RepoOverview isActive={key === 'overview'} repo={repo} />}
                    </Tab.Pane>
                    <Tab.Pane eventKey="tags">
                        <RepoTags isActive={key === 'tags'} />
                    </Tab.Pane>
                </Tab.Content>
            </Tab.Container>
        </div>
    );
};