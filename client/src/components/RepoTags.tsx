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

    const orderByOptionToQueryParams = (orderByValue: string) => {
        switch (orderByValue) {
            case "Newest": return ['last_push', 'desc'];
            case "Oldest": return ['last_push', 'asc'];
            case "Name A-Z": return ['name', 'asc'];
            case "Name Z-A": return ['name', 'desc'];
            default: return [null, 'asc'];
        }
    }

    const filter = () => {
        const [sort_by, sort_order] = orderByOptionToQueryParams(orderBy);
        const pagination = new PaginationParams(1, 10, sort_by, sort_order);

        TagsService.FilterTagsOfRepo(props.repo.canonical_name, filterText, pagination).then((res) => {
            console.log(res.data);
        }).catch((err: AxiosError) => {
            console.error(err);
        });
    }

    return (
        <div className="tab-pane fade show active" id="tags">
            <div className="d-flex align-items-center mb-1">
                {/* Order by */}
                <span>Order by</span>
                <select
                    id="orgSelect"
                    className="form-select d-inline ms-2 w-auto"
                    value={orderBy}
                    onChange={e => setOrderBy(e.target.value)}>
                    {Array.from(orderByOptions!.entries()).map(([id, name]) => (
                        <option key={id} value={name}>
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