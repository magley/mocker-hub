import React, { useEffect, useState } from 'react';
import { AxiosError, AxiosResponse } from 'axios';
import { LogLevel, LogQueryDTO, LogsService } from '../api/logs.api';
import Spinner from 'react-bootstrap/Spinner';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { Row, Col, Table } from 'react-bootstrap';
import { Pagination } from 'react-bootstrap';
import "./Analytics.css";
import ReactMarkdown from 'react-markdown';
import { AnalyticsSidebar } from '../components/AnalyticsSidebar';
import { log } from 'console';

export const Analytics = () => {
    const [query, setQuery] = useState("");
    const [pageNumber, setPageNumber] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [sortBy, setSortBy] = useState('date_time');
    const [sortAscending, setSortAscending] = useState(true);
    const [logs, setLogs] = useState<LogQueryDTO | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showSidebar, setShowSidebar] = useState<boolean>(false);

    const getSortIcon = (column: string) => {
        if (sortBy !== column) return null;
        return sortAscending ? '▲' : '▼';
    };

    const getLevelVariant = (level: string) => {
        switch (level.toLowerCase()) {
            case 'error':
                return 'danger';
            case 'warning':
                return 'warning';
            case 'info':
                return 'info';
            case 'debug':
                return 'primary';
            default:
                return 'secondary';
        }
    };

    const handleSearch = async () => {
        if (query == "") {
            setLogs(null);
            setError('');
            return;
        }
        if (logs === null || logs.hits.length == 0) {
            setLoading(true);
        }

        setError('');

        LogsService.Search(query, pageNumber, pageSize, sortBy, sortAscending).then((res: AxiosResponse<LogQueryDTO>) => {
            setLogs(res.data);
            if (res.data.info.page > res.data.info.total_pages) {
                handlePageChange(res.data.info.total_pages);
            }
        }).catch((err: AxiosError) => {
            setError(err.message || 'Failed to fetch logs');
            setLogs(null);
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
        if (!logs || logs.info.total_pages <= 1) return null;

        const items = [];
        const maxPagesToShow = 10;
        const startPage = Math.max(1, logs.info.page - Math.floor(maxPagesToShow / 2));
        const endPage = Math.min(logs.info.total_pages, startPage + maxPagesToShow - 1);

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
                disabled={logs.info.page <= 1}
                onClick={() => handlePageChange(logs.info.page - 1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );


        for (let page = startPage; page <= endPage; page++) {
            items.push(
                <Pagination.Item
                    key={page}
                    active={page === logs.info.page}
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
                disabled={logs.info.page >= logs.info.total_pages}
                onClick={() => handlePageChange(logs.info.page + 1)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        items.push(
            <Pagination.Last
                key="prev"
                onClick={() => handlePageChange(logs.info.total_pages)}
                style={{ width: '48px', textAlign: 'center' }}
            />
        );

        return <Pagination>{items}</Pagination>;
    };

    return (
        <div className="page-container" style={{ padding: '2rem' }}>
            <div className="main-content">
                <h2 className="text-center">
                    <i className="bi-graph-up"></i> Log Search
                </h2>

                <Form className="mb-3" onSubmit={(e) => {
                    e.preventDefault(); // Prevent page reload
                    handleSearch();     // Trigger search logic
                }}>
                    <Row className="g-3 align-items-end">
                        <Col xs={0}>
                            <Form.Group controlId="searchQuery">
                                <Form.Label>Search Query</Form.Label>
                                <Form.Control
                                    type="text"
                                    placeholder="Enter search query"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                />
                            </Form.Group>
                        </Col>

                        <Col xs="auto">
                            <Button variant="primary" type="submit">
                                <i className="bi bi-search"></i>
                            </Button>
                        </Col>

                        <Col xs="auto">
                            <Button variant="primary" onClick={() => setShowSidebar(!showSidebar)}>
                                <i className="bi bi-patch-question-fill"></i>
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
                        <p>
                            Make sure keywords are <b>not wrapped in quotes</b>.
                            <br />
                            Make sure log levels, dates and words/phrases <b>are wrapped in quotes</b>.
                            <br />
                            Make sure you don't have dangling parentheses.
                            <br />
                        </p>
                    </>
                }

                {logs !== null && (
                    <>
                        {logs.hits.length === 0 ? (
                            <div className="mt-4 text-muted">
                                <h5>No results found</h5>
                                <p>Try adjusting your query or filters to find matching logs.</p>
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

                                {/* Log count */}
                                <div>
                                    Showing <strong>{logs.hits.length}</strong> of <strong>{logs.info.total_hits}</strong> results on
                                    page <strong>{logs.info.page}</strong> of <strong>{logs.info.total_pages}</strong>
                                </div>

                                {/* Table */}
                                <div style={{ maxHeight: '600px', overflowY: 'auto', overflowX: 'auto' }}>
                                    <Table striped bordered hover responsive style={{ tableLayout: 'fixed', width: '100%' }}>
                                        <thead>
                                            <tr>
                                                <th style={{ width: '200px', cursor: 'pointer' }} onClick={() => handleSort('date_time')}>
                                                    Timestamp {getSortIcon('date_time')}
                                                </th>
                                                <th style={{ width: '120px', cursor: 'pointer' }} onClick={() => handleSort('log_level')}>
                                                    Level {getSortIcon('log_level')}
                                                </th>
                                                <th style={{ width: '600px' }}>Message</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {logs.hits.map((log, index) => (
                                                <tr key={index}>
                                                    <td>{new Date(log.date_time).toLocaleString()}</td>
                                                    <td>
                                                        <span className={`badge bg-${getLevelVariant(log.level.toString())}`}>
                                                            {log.level}
                                                        </span>
                                                    </td>
                                                    <td>{log.text}</td>
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

            {
                showSidebar && (
                    <AnalyticsSidebar onClose={() => setShowSidebar(false)} />
                )
            }
        </div >
    );
};
