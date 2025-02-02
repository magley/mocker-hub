import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Row, Spinner } from 'react-bootstrap';
import { RepositoryService, ReposOfUserDTO } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import './RepoOfUser.css';
import { getJwtId } from '../util/localstorage';
import { RepoPreview } from '../components/RepoPreview';

export const RepoStarred: React.FC = () => {
    const [fullResult, setFullResult] = useState<ReposOfUserDTO>();
    const [orgNames, setOrgNames] = useState<Map<number, string>>();
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const { username } = useParams<{ username: string }>();
    const [myId, setMyId] = useState<number>();

    let navigate = useNavigate();

    useEffect(() => {
        fetchRepos();

        setMyId(getJwtId());
    }, []);

    const fetchRepos = () => {
        if (username === undefined) {
            navigate(`/`);
            return;
        }

        RepositoryService.GetStarredRepositories(username).then((res: AxiosResponse<ReposOfUserDTO>) => {
            setLoading(false);
            setFullResult(res.data);

            const orgNamesMap = new Map(Object.entries(res.data.organization_names).map(([key, value]) => [Number(key), value]));
            setOrgNames(orgNamesMap);

        }).catch((err: AxiosError) => {
            setLoading(false);
            setError((err.response?.data as any)["detail"]["message"]);
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
            {/* Page Title */}
            {fullResult?.user_id == myId ? (<h1>Your starred repositories</h1>) : (<h1>{fullResult!.user_name}'s starred repositories</h1>)}
            
            {
                fullResult?.repos.map((repo) => (
                    <RepoPreview key={repo.id} repo={repo} orgNames={orgNames} />
                ))
            }
        </Row >
    );
};