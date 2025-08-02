import React, { useEffect, useState } from "react";
import { RepoPreview } from "./RepoPreview";
import { AxiosResponse, AxiosError } from "axios";
import { Spinner, Row, Button } from "react-bootstrap";
import { Link } from "react-router-dom";
import { RepoDTO, RepositoryService, RepositoryBadge } from "../api/repo.api";
import { BadgeUtils } from "../util/badge";
import { getJwtId } from "../util/localstorage";
import { OrganizationDTOBasic } from "../api/org.api";

export const OrgRepositories: React.FC<{ isActive: boolean, org: OrganizationDTOBasic, amIMemberOfOrg: boolean }> = ({ isActive, org, amIMemberOfOrg }) => {
    useEffect(() => {
        if (isActive) { }
    }, [isActive]);

    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [myId, setMyId] = useState<number>();

    const [repositories, setRepositories] = useState<RepoDTO[]>([]);
    const [filteredRepos, setFilteredRepos] = useState<RepoDTO[]>([]);

    const [searchTerm, setSearchTerm] = useState('');
    const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
    const [showPublic, setShowPublic] = useState(false);
    const [showPrivate, setShowPrivate] = useState(false);

    const [showBadgeOfficial, setShowBadgeOfficial] = useState(false);
    const [showBadgeVerified, setShowBadgeVerified] = useState(false);
    const [showBadgeSponsoredOSS, setShowBadgeSponsoredOSS] = useState(false);

    useEffect(() => {
        fetchRepos();
        setMyId(getJwtId());
    }, []);

    const fetchRepos = () => {
        RepositoryService.GetAllByOrganizationId(org.id).then((res: AxiosResponse<RepoDTO[]>) => {
            setLoading(false);
            setRepositories(res.data);
            setFilteredRepos(res.data);
        }).catch((err: AxiosError) => {
            setLoading(false);
            setError((err.response?.data as any)["detail"]["message"]);
        })
    }

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        filterRepos(e.target.value, showPublic, showPrivate);
    };

    const toggleAdvancedSearch = () => {
        setShowAdvancedSearch(!showAdvancedSearch);
    };

    const handlePublicChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowPublic(e.target.checked);
        filterRepos(searchTerm, e.target.checked, showPrivate, showBadgeOfficial, showBadgeVerified, showBadgeSponsoredOSS);
    };

    const handlePrivateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowPrivate(e.target.checked);
        filterRepos(searchTerm, showPublic, e.target.checked, showBadgeOfficial, showBadgeVerified, showBadgeSponsoredOSS);
    };

    const handleBadgeOfficialChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowBadgeOfficial(e.target.checked);
        filterRepos(searchTerm, showPublic, showPrivate, e.target.checked, showBadgeVerified, showBadgeSponsoredOSS);
    };

    const handleBadgeVerifiedChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowBadgeVerified(e.target.checked);
        filterRepos(searchTerm, showPublic, showPrivate, showBadgeOfficial, e.target.checked, showBadgeSponsoredOSS);
    };

    const handleBadgeSponsoredOSSChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowBadgeSponsoredOSS(e.target.checked);
        filterRepos(searchTerm, showPublic, showPrivate, showBadgeOfficial, showBadgeVerified, e.target.checked);
    };

    const filterRepos = (searchTerm: string, showPublic?: boolean, showPrivate?: boolean, showBadgeOfficial?: boolean, showBadgeVerified?: boolean, showBadgeSponsoredOSS?: boolean) => {
    const noBadgeFiltersSelected = !showBadgeOfficial && !showBadgeVerified && !showBadgeSponsoredOSS;
    const noVisibilityFiltersSelected = !showPublic && !showPrivate;

    const filtered = repositories.filter((repo) => {
        const matchesSearch =
            repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (repo.desc && repo.desc.toLowerCase().includes(searchTerm.toLowerCase()));
        const matchesVisibility = noVisibilityFiltersSelected
            || (showPublic && repo.public)
            || (showPrivate && !repo.public);
        const matchesBadge = noBadgeFiltersSelected
            || (repo.badge === RepositoryBadge.official && showBadgeOfficial)
            || (repo.badge === RepositoryBadge.verified && showBadgeVerified)
            || (repo.badge === RepositoryBadge.sponsored_oss && showBadgeSponsoredOSS);

        return (matchesSearch && matchesVisibility && matchesBadge);
    });

    setFilteredRepos(filtered);
};

    const badgeDataBundle = [
        {
            type: RepositoryBadge.official,
            checked: showBadgeOfficial,
            onChange: handleBadgeOfficialChange,
            id: "officialCheckbox",
        },
        {
            type: RepositoryBadge.verified,
            checked: showBadgeVerified,
            onChange: handleBadgeVerifiedChange,
            id: "verifiedCheckbox",
        },
        {
            type: RepositoryBadge.sponsored_oss,
            checked: showBadgeSponsoredOSS,
            onChange: handleBadgeSponsoredOSSChange,
            id: "sponsoredOSSCeckbox",
        },
    ];


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

            { repositories.length >= 1 ? (
                <>
                <div className="d-flex justify-content-between">
                    <div className="d-flex align-items-center flex-grow-1 me-3" style={{ maxWidth: "70%" }}>
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

                    {/* Add new repo Button */}
                    {amIMemberOfOrg && (
                        <Link to={`/new/org/${org.id}`}>
                            <Button className="btn btn-primary">
                                    Create Repository
                            </Button>
                        </Link>
                    )}
                </div>
        
                {/* Advanced Search Section */}
                {showAdvancedSearch && (
                    <div className="advanced-search">
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

                        {/* Badges - Checkbox for each badge type. */}
                        {badgeDataBundle.map((badge) => (
                            <div className="mb-3">
                                <div className="form-check ms-2 d-flex align-items-center">
                                    <input
                                        type="checkbox"
                                        className="form-check-input form-check-lg"
                                        checked={badge.checked}
                                        onChange={badge.onChange}
                                        id={badge.id}
                                    />
                                    <label className="form-check-label fs-5 ms-2" htmlFor={badge.id}>
                                        <span className={`badge rounded-pill ${BadgeUtils.toBootstrapColor(badge.type)}`}>
                                            <i className={`bi ${BadgeUtils.toBootstrapIcon(badge.type)}`}> </i>
                                            {BadgeUtils.toHumanText(badge.type)}
                                        </span>
                                    </label>
                                </div>
                            </div>
                        ))}
                    </div >
                )
                }

                {
                    filteredRepos.map((repo) => (
                        <RepoPreview key={repo.id} repo={repo} orgNames={undefined} showCanonical={false} />
                    ))
                }
                </>
            ) : ( <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                No repositories created yet.
                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>

                        {amIMemberOfOrg && (
                        <Link to={`/new/org/${org.id}`}>
                            <Button className="btn btn-primary">
                                    Create Repository
                            </Button>
                        </Link>
                    )}
                    </div>
                 </div>
             ) }

        </Row>
    );
}