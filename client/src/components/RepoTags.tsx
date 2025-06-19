import React, { useEffect, useState } from 'react';
import { Button, Card, Col, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { TagDTO, TagsService } from '../api/tags.api';
import { RepoExtDTO } from '../api/repo.api';
import { PaginationParams } from '../util/pagination';
import { AxiosError } from 'axios';
import { formatDistanceToNow } from 'date-fns';
import ResponsivePagination from 'react-responsive-pagination';
import { NavLink } from 'react-router-dom';
import { ToastType, useToastStore } from '../util/toastStore';


export const RepoTags: React.FC<{ isActive: boolean, repo: RepoExtDTO }> = (props) => {
    const orderByOptions = [
        "Newest", "Oldest", "Name A-Z", "Name Z-A"
    ]
    const [filterText, setFilterText] = useState<string>("");
    const [orderBy, setOrderBy] = useState<string>(orderByOptions[0]);
    const [tags, setTags] = useState<TagDTO[]>([]);
    const [error, setError] = useState<string | null>(null);

    const [itemsPerPage, setItemsPerPage] = useState<number>(10);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const addToast = useToastStore((state) => state.addToast);
    const [deletingTag, setDeletingTag] = useState<string | null>(null);

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

    const handlePageChange = (newPage: number) => {
        setCurrentPage(newPage);
        filterWithPage(newPage);
    }

    const filter = () => {
        filterWithPage(currentPage);
    }

    const filterWithPage = (page: number) => {
        const [sort_by, sort_order] = orderByOptionToQueryParams(orderBy);
        const pagination = new PaginationParams(page, itemsPerPage, sort_by, sort_order);

        TagsService.FilterTagsOfRepo(props.repo.canonical_name, filterText, pagination).then((res) => {
            setError(null);
            setTags(res.data.items);
            setTotalPages(Math.ceil(res.data.total_count / itemsPerPage));
        }).catch((err: AxiosError) => {
            setError(`${err}`);
            setTags([]);
        });
    }

    const handleDeleteTag = async (tag: TagDTO) => {
        setDeletingTag(tag.name); 

        TagsService.DeleteTag({ repo_id: props.repo.id, tag_name: tag.name })
            .then((res) => {
                addToast(res.data.message, ToastType.success);
                setTags(currentTags => currentTags.filter(t => t.name !== tag.name));
            })
            .catch((err: AxiosError) => {
                const data = (err.response?.data ?? {}) as any;
                const msg = typeof data.detail === 'string' ? data.detail : data.detail?.message;
                addToast(msg, ToastType.error);
            })
            .finally(() => { 
                setDeletingTag(null); 
            });
    };

    return (
        <div className="tab-pane fade show active m-5" id="tags">
            {/* Error? */}
            {error && <div className='error'>{error}</div>}

            {/* Filtering */}
            <div className="d-flex align-items-center mb-5">
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

            {/* Results */}
            {
                tags.map((tag) => (
                    <Col key={tag.id} xs={12}>
                        <Card className="m-3">
                            <Card.Body className="d-flex justify-content-between align-items-center">
                                <div>
                                    {/* Tag title */}
                                    <Card.Title style={{ fontSize: '0.8rem' }}>Tag</Card.Title>

                                    {/* Tag name */}
                                    <Card.Subtitle style={{ fontSize: '1.2rem' }}>{tag.name}</Card.Subtitle>

                                    {/* Last pushed */}
                                    <Card.Text className="mt-1 mb-2 text-muted" style={{ fontSize: '0.8rem' }}>
                                        Last pushed <OverlayTrigger
                                            placement="top"
                                            overlay={<Tooltip>{new Date(tag.last_push).toLocaleString()}</Tooltip>}>
                                            <b>{formatDistanceToNow(new Date(tag.last_push), { addSuffix: true })}</b>
                                        </OverlayTrigger> by <NavLink to={`/u/${tag.last_pushed_by_username}/repos`}>{tag.last_pushed_by_username}</NavLink>
                                    </Card.Text>

                                    {/* ... */}
                                    <Card.Text style={{ fontSize: '0.8rem' }}>
                                    </Card.Text>
                                </div>

                                {/* Delete tag */}
                                {/* We can reuse `can_update` as `can_delete_tag` since the access-control logic is identical. */}
                                {props.repo?.can_update && tag.name &&
                                    <Button variant="danger" className="me-2" onClick={() => handleDeleteTag(tag)} title="Delete tag" disabled={deletingTag === tag.name}>
                                        {deletingTag === tag.name
                                            ? (<output><span className="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Deleting...</output>)
                                            : <><i className="bi bi-trash" />Delete</>
                                        }
                                    </Button>
                                }
                            </Card.Body>
                        </Card>
                    </Col>
                ))
            }

            { /* Pagination */}
            <ResponsivePagination
                total={totalPages}
                current={currentPage}
                onPageChange={page => handlePageChange(page)}
            />
        </div>
    );
};