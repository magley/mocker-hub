import React, { useEffect, useState } from 'react';
import { Nav, Spinner, Tab } from 'react-bootstrap';
import { RepoOverview } from '../components/RepoOverview';
import { RepoTags } from '../components/RepoTags';
import { NavLink, useParams } from 'react-router-dom';
import { RepoDTO, RepositoryService } from '../api/repo.api';
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
    const [repo, setRepo] = useState<RepoDTO>();
    const [key, setKey] = useState<string>('overview');
    const [loading, setLoading] = useState<boolean>(true);
    const [repoOwner, setRepoOwner] = useState<RepoOwner>({
        name: '...',
        id: 1,
        isUser: true,
        official: false,
        linkURL: "."
    });

    useEffect(() => {
        RepositoryService.GetRepoByCanonicalName(repoName!).then((res: AxiosResponse<RepoDTO>) => {
            setRepo(res.data);
            setLoading(false);

            if (res.data.organization_id === null) {
                // setRepoOwner({
                //     res.data.owner_id,
                //     "",
                //     true
                // });
            }

        }).catch((err: AxiosError) => {
            if (err.response?.status == 404) {
                console.error("Not found");
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
                <h1>{repo?.canonical_name}</h1>
                <h5>By <NavLink to={repoOwner.linkURL}>{repoOwner.name}</NavLink></h5>
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