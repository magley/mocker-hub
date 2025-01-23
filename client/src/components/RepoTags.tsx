import React, { useEffect, useState } from 'react';
import { Button } from 'react-bootstrap';
import { TagsService } from '../api/tags.api';
import { RepoExtDTO } from '../api/repo.api';
import { PaginationParams } from '../util/pagination';
import { AxiosError } from 'axios';

export const RepoTags: React.FC<{ isActive: boolean, repo: RepoExtDTO }> = (props) => {
    const orderByOptions = [
        "Newest", "Oldest", "Name A-Z", "Name Z-A"
    ]
    const [filterText, setFilterText] = useState<string>("");
    const [orderBy, setOrderBy] = useState<string>(orderByOptions[0]);

    useEffect(() => {
        if (props.isActive) {
            filter();
        }
    }, [props.isActive]);

    const filter = () => {
    }


    return (
        <div className="tab-pane fade show active" id="tags">
            <div className="d-flex align-items-center mb-1">
                {/* Order by */}
                <span>Order by</span>
                <select
                    id="orgSelect"
                    className="form-select d-inline ms-2 w-auto"
                    value={orderBy || ''}
                    onChange={e => setOrderBy(e.target.value)}>
                    {Array.from(orderByOptions!.entries()).map(([id, name]) => (
                        <option key={id} value={id}>
                            {name}
                        </option>
                    ))}
                </select>

                {/* Filter by text */}
                <input
                    type="text"
                    className="form-control d-inline ms-5 w-auto"
                    placeholder="Filter tags"
                    value={filterText}
                    onChange={e => setFilterText(e.target.value)}
                />

                {/* Submit */}
                <Button
                    className="btn btn-primary d-inline ms-5 w-auto"
                    onClick={filter}
                >
                    <i className="bi bi-search"></i> Search
                </Button>
            </div>
        </div>
    );
};