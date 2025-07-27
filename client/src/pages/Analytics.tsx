import React, { useState } from 'react';
import { AxiosError, AxiosResponse } from 'axios';
import { LogQueryDTO, LogsService } from '../api/logs.api';

export const Analytics = () => {
    const [query, setQuery] = useState('log_level == "info"');
    const [pageNumber, setPageNumber] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [sortBy, setSortBy] = useState('timestamp');
    const [sortAscending, setSortAscending] = useState(true);
    const [logs, setLogs] = useState<LogQueryDTO | null>(null);
    // const [totalResults, setTotalResults] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async () => {
        setLoading(true);
        setError('');

        LogsService.Search(query, pageNumber, pageSize, sortBy, sortAscending).then((res: AxiosResponse<LogQueryDTO>) => {
            console.log(res.data);
            setLogs(res.data);
        }).catch((err: AxiosError) => {
            setError(err.message || 'Failed to fetch logs');
            setLogs(null);
        }).finally(() => {
            setLoading(false);
        });

    };

    return (
        <div style={{ padding: '2rem' }}>
            <h2>Log Search</h2>
            <div style={{ marginBottom: '1rem' }}>
                <input
                    type="text"
                    placeholder="Search query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />
                <input
                    type="number"
                    placeholder="Page number"
                    value={pageNumber}
                    onChange={(e) => setPageNumber(Number(e.target.value))}
                />
                <input
                    type="number"
                    placeholder="Page size"
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                />
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                    <option value="date_time">Timestamp</option>
                    <option value="log_level">Level</option>
                </select>
                <label>
                    <input
                        type="checkbox"
                        checked={sortAscending}
                        onChange={(e) => setSortAscending(e.target.checked)}
                    />
                    Sort Ascending
                </label>
                <button onClick={handleSearch}>Search</button>
            </div>

            {loading && <p>Loading...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {logs !== null &&
                <span>

                    <ul>
                        {logs.hits.map((log, index) => (
                            <li key={index}>
                                <strong>{log.date_time}</strong> [{log.level}] - {log.text}
                            </li>
                        ))}
                    </ul>

                    <div>
                        Page {logs.info.page} of {logs.info.total_pages} <br />
                        Showing {logs.info.page_size} of {logs.info.total_hits} logs <br />
                    </div>

                </span>
            }
        </div >
    );
};