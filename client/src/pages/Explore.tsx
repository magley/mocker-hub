import React, { useEffect, useState } from 'react';
import { Row, Spinner, Button, Pagination, Form } from 'react-bootstrap';
import { RepositoryBadge, RepositoryQueryDTO, RepositoryService } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import './RepoOfUser.css';
import { RepoPreview } from '../components/RepoPreview';
import { BadgeUtils } from '../util/badge';

export const Explore: React.FC = () => {
    const [orgNames, setOrgNames] = useState<Map<number, string>>();
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const [repositories, setRepositories] = useState<RepositoryQueryDTO | null>(null);

    const [searchTerm, setSearchTerm] = useState('');
    const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);

    const [showBadgeOfficial, setShowBadgeOfficial] = useState(false);
    const [showBadgeVerified, setShowBadgeVerified] = useState(false);
    const [showBadgeSponsoredOSS, setShowBadgeSponsoredOSS] = useState(false);

    const [pageNumber, setPageNumber] = useState(1);
    const [pageSize, setPageSize] = useState(10);

    useEffect(() => {
        fetchRepos();
    }, [pageNumber, pageSize, showBadgeOfficial, showBadgeVerified, showBadgeSponsoredOSS]);

    const handleSearch = async () => {
        setPageNumber(1); 
        fetchRepos();
    }

    const fetchRepos = () => {
        if (repositories === null || repositories.hits.length == 0) {
            setLoading(true);
        }

        setError('');

        RepositoryService.GetPublicRepositories(searchTerm, pageNumber, pageSize, showBadgeOfficial, showBadgeSponsoredOSS, showBadgeVerified).then((res: AxiosResponse<RepositoryQueryDTO>) => {
            setRepositories(res.data);
            if (res.data.info.page > res.data.info.total_pages) {
                handlePageChange(res.data.info.total_pages);
            }
            const orgNamesMap = new Map(Object.entries(res.data.organization_names).map(([key, value]) => [Number(key), value]));
            setOrgNames(orgNamesMap);
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
            setRepositories(null);
        }).finally(() => {
            setLoading(false);
        });
    }

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
    };

    const handlePageChange = (page: number) => {
        setPageNumber(page);
    };

    const toggleAdvancedSearch = () => {
        setShowAdvancedSearch(!showAdvancedSearch);
    };

    const handleBadgeOfficialChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowBadgeOfficial(e.target.checked);
    };

    const handleBadgeVerifiedChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowBadgeVerified(e.target.checked);
    };

    const handleBadgeSponsoredOSSChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setShowBadgeSponsoredOSS(e.target.checked);
    };

    const renderPagination = () => {
        if (!repositories || repositories.info.total_pages <= 1) return null;

        const items = [];
        const maxPagesToShow = 10;
        const startPage = Math.max(1, repositories.info.page - Math.floor(maxPagesToShow / 2));
        const endPage = Math.min(repositories.info.total_pages, startPage + maxPagesToShow - 1);

        items.push(
            <Pagination.First
                key="first"
                onClick={() => handlePageChange(1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        items.push(
            <Pagination.Prev
                key="prev"
                disabled={repositories.info.page <= 1}
                onClick={() => handlePageChange(repositories.info.page - 1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );


        for (let page = startPage; page <= endPage; page++) {
            items.push(
                <Pagination.Item
                    key={page}
                    active={page === repositories.info.page}
                    onClick={() => handlePageChange(page)}
                    style={{ width: '48px', textAlign: 'center' }}
                >
                    {page}
                </Pagination.Item>
            );
        }

        items.push(
            <Pagination.Next
                key="next"
                disabled={repositories.info.page >= repositories.info.total_pages}
                onClick={() => handlePageChange(repositories.info.page + 1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        items.push(
            <Pagination.Last
                key="last"
                onClick={() => handlePageChange(repositories.info.total_pages)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        return <Pagination>{items}</Pagination>;
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
            <h1>Explore Repositories</h1>
            <>
                <div className="d-flex justify-content-between">
                    <div className="d-flex align-items-center flex-grow-1 me-3">
                        {/* Search Bar */}
                        <input
                            type="text"
                            className="form-control me-2"
                            placeholder="Search repositories"
                            value={searchTerm}
                            onChange={handleSearchChange}
                        />
                         <Button variant="primary" className="me-5" type="submit" onClick={handleSearch}>
                            <i className="bi bi-search"></i>
                        </Button>
                        {/* Advanced Search Button */}
                        <Button className="btn btn-primary" onClick={toggleAdvancedSearch}>
                            {showAdvancedSearch ? <i className="bi bi-funnel-fill"></i> : <i className="bi bi-funnel"></i>}
                        </Button>
                    </div>
                </div>
    
                {/* Advanced Search Section */}
                {showAdvancedSearch && (
                    <div className="advanced-search">

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
                    </div>
                    ) 
                }
            </>

            {repositories !== null && (
                <>
                    {repositories.hits.length === 0 ? (
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            Not found any repositories.
                        </div>
                    ) : (
                    <>
                    {/* Pagination */}
                        <div className="d-flex flex-wrap gap-3 mt-3 align-items-start">
                            <div>{renderPagination()}</div>

                            {/* Page size dropdown with inline label */}
                            <div className="d-flex align-items-center gap-2">
                                <label htmlFor="pageSizeSelect" className="mb-0">Rows per page:</label>
                                <Form.Select
                                    id="pageSizeSelect"
                                    value={pageSize}
                                    onChange={(e) => {
                                        setPageSize(Number(e.target.value));
                                        setPageNumber(1);
                                    }}
                                    style={{ width: '100px' }}
                                >
                                    {[5, 10, 25, 50, 100].map((size) => (
                                        <option key={size} value={size}>{size}</option>
                                    ))}
                                </Form.Select>
                            </div>
                        </div>

                        {/* Repo count */}
                        <div>
                            Showing <strong>{repositories.hits.length}</strong> of <strong>{repositories.info.total_hits}</strong> results on
                            page <strong>{repositories.info.page}</strong> of <strong>{repositories.info.total_pages}</strong>
                        </div>

                        {/* Show repositories */}
                        <>
                            {repositories.hits.map((repo) => (
                                <RepoPreview key={repo.id} repo={repo} orgNames={orgNames} showCanonical={true} />
                            ))}
                        </>
                    </>
                    )}
                </>
            )}
        </Row>
    );
};