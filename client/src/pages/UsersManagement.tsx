import React, { useEffect, useState } from 'react';
import { AxiosError, AxiosResponse } from 'axios';
import Spinner from 'react-bootstrap/Spinner';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { Row, Col, Table } from 'react-bootstrap';
import { Pagination } from 'react-bootstrap';
import "./Analytics.css";
import { UserQueryDTO, UserService } from '../api/user.api';
import { Link } from 'react-router-dom';

export const UsersManagement = () => {
    const [searchTerm, setSearchTerm] = useState("");
    const [pageNumber, setPageNumber] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [sortBy, setSortBy] = useState('username');
    const [sortAscending, setSortAscending] = useState(true);
    const [loading, setLoading] = useState(false);
    const [users, setUsers] = useState<UserQueryDTO | null>(null);
    const [error, setError] = useState('');

    const getSortIcon = (column: string) => {
        if (sortBy !== column) return null;
        return sortAscending ? '▲' : '▼';
    };

    const handleSearch = async () => {
        //todo fetch all users on load?
        if (searchTerm == "") {
            setUsers(null);
            setError('');
            return;
        }
        if (users === null || users.hits.length == 0) {
            setLoading(true);
        }

        setError('');

        UserService.SearchUsersPaginated(searchTerm, pageNumber, pageSize, sortBy, sortAscending).then((res: AxiosResponse<UserQueryDTO>) => {
            setUsers(res.data);
            if (res.data.info.page > res.data.info.total_pages) {
                handlePageChange(res.data.info.total_pages);
            }
        }).catch((err: AxiosError) => {
            setError(err.message || 'Failed to fetch users');
            setUsers(null);
        }).finally(() => {
            setLoading(false);
        });
    };

    const handleSort = (column: string) => {
        if (sortBy === column) {
            setSortAscending(!sortAscending);
        } else {
            setSortBy(column);
            setSortAscending(true);
        }
        handleSearch();
    };

    const handlePageChange = (page: number) => {
        setPageNumber(page);
    };

    useEffect(() => {
        handleSearch();
    }, [pageNumber]);
    useEffect(() => {
        handleSearch();
    }, [pageSize]);

    const renderPagination = () => {
        if (!users || users.info.total_pages <= 1) return null;

        const items = [];
        const maxPagesToShow = 10;
        const startPage = Math.max(1, users.info.page - Math.floor(maxPagesToShow / 2));
        const endPage = Math.min(users.info.total_pages, startPage + maxPagesToShow - 1);

        items.push(
            <Pagination.First
                key="prev"
                onClick={() => handlePageChange(1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        items.push(
            <Pagination.Prev
                key="prev"
                disabled={users.info.page <= 1}
                onClick={() => handlePageChange(users.info.page - 1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );


        for (let page = startPage; page <= endPage; page++) {
            items.push(
                <Pagination.Item
                    key={page}
                    active={page === users.info.page}
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
                disabled={users.info.page >= users.info.total_pages}
                onClick={() => handlePageChange(users.info.page + 1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        items.push(
            <Pagination.Last
                key="prev"
                onClick={() => handlePageChange(users.info.total_pages)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        return <Pagination>{items}</Pagination>;
    };

    return (
        <div className="page-container" style={{ padding: '2rem' }}>
            <div className="main-content">
                <h2 className="text-center">
                    <i className="bi-people"></i> User Management
                </h2>

                <Form className="mb-3" onSubmit={(e) => {
                    e.preventDefault(); // Prevent page reload
                    handleSearch();     // Trigger search logic
                }}>
                    <Row className="g-3 align-items-end">
                        <Col xs={0}>
                            <Form.Group controlId="searchQuery">
                                <Form.Label>Search users</Form.Label>
                                <Form.Control
                                    type="text"
                                    placeholder="Enter username"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </Form.Group>
                        </Col>

                        <Col xs="auto">
                            <Button variant="primary" type="submit">
                                <i className="bi bi-search"></i>
                            </Button>
                        </Col>
                    </Row>
                </Form>


                {loading && <Spinner animation="border" variant="primary" role="status"></Spinner>}
                {error &&
                    <>
                        <p style={{ color: 'red' }}>
                            Something went wrong ({error}).
                            <br />
                            Check the console for more info.
                        </p>
                    </>
                }

                {users !== null && (
                    <>
                        {users.hits.length === 0 ? (
                            <div className="mt-4 text-muted">
                                <h5>No results found</h5>
                            </div>
                        ) : (
                            <>
                                <div className="d-flex flex-wrap gap-3 mt-3 align-items-start">
                                    {/* Pagination */}
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

                                {/* User count */}
                                <div>
                                    Showing <strong>{users.hits.length}</strong> of <strong>{users.info.total_hits}</strong> results on
                                    page <strong>{users.info.page}</strong> of <strong>{users.info.total_pages}</strong>
                                </div>

                                {/* Table */}
                                <div style={{ maxHeight: '600px', overflowY: 'auto', overflowX: 'auto' }}>
                                    <Table striped bordered hover responsive style={{ tableLayout: 'fixed', width: '100%' }}>
                                        <thead>
                                            <tr>
                                                <th style={{ width: '180px', cursor: 'pointer' }} onClick={() => handleSort('username')}>
                                                    Username {getSortIcon('username')}
                                                </th>
                                                <th style={{ width: '200px', cursor: 'pointer' }} onClick={() => handleSort('full_name')}>
                                                    Full Name {getSortIcon('full_name')}
                                                </th>
                                                <th style={{ width: '220px', cursor: 'pointer' }} onClick={() => handleSort('email')}>
                                                    Email {getSortIcon('email')}
                                                </th>
                                                <th style={{ width: '320px', cursor: 'pointer' }} onClick={() => handleSort('badge')}>
                                                    Badge {getSortIcon('badge')}
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {users.hits.map((user, index) => (
                                                <tr key={index}>
                                                    <td><Link to={`/u/${user.username}`} className="fw-bold text-primary" 
                                                        style={{ textDecoration: "none", cursor: "pointer" }}>
                                                        {user.username}
                                                    </Link></td>
                                                    <td>{user.first_name} {user.last_name}</td>
                                                    <td>{user.email}</td>
                                                    //todo decorate the badge
                                                    <td>{user.badge}</td>
                                                    //todo add edit button and a correponding dialog
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                </div>
                            </>
                        )}
                    </>
                )}
            </div >
        </div >
    );
};
