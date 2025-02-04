import React from 'react';
import { RepoDTO, RepositoryBadge } from '../api/repo.api';
import { Card, Col, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { RepositoryService } from '../api/repo.api';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

export const RepoPreview: React.FC<{ repo: RepoDTO, orgNames: Map<number, string> | undefined }> = ( {repo, orgNames} ) => {
    return (
        <Col key={repo.id} xs={12}>
            <Card>
                <Card.Body>
                    {/* Repository Title with React Router Link */}
                    <Card.Title>
                        <Link to={`/r/${repo.canonical_name}`} className="text-primary">
                            <span>{repo.name}</span>
                        </Link>
                        {/* Private */}
                        {!repo.public && (
                            <span className="badge rounded-pill bg-secondary" style={{ fontSize: '0.7rem', marginLeft: '1em' }}>
                                <i className="bi bi-lock"></i>
                                Private
                            </span>
                        )}
                        {/* Badge */}   
                        {repo && repo?.badge !== RepositoryBadge.none &&
                            <span
                                className={`badge rounded-pill ${RepositoryService.BadgeToBootstrapColor(repo?.badge)}`}
                                style={{ fontSize: '0.7rem', marginLeft: '1em' }}
                            >
                                <i className={`bi ${RepositoryService.BadgeToHumanBootstrapIcon(repo?.badge)}`}> </i>
                                {RepositoryService.BadgeToHumanText(repo?.badge)}
                            </span>
                        }
                    </Card.Title>

                    {/* Organization Name (if exists) */}
                    {repo.organization_id && (
                        <Card.Subtitle className="mb-2 text-muted" style={{ fontSize: '0.8rem' }}>
                            Part of organization {orgNames?.get(repo.organization_id)}
                        </Card.Subtitle>
                    )}

                    {/* Last update */}
                    {repo.last_updated && (
                        <Card.Text style={{ fontSize: '0.8rem' }}>
                            Updated <OverlayTrigger
                                placement="top"
                                overlay={<Tooltip>{new Date(repo.last_updated).toLocaleString()}</Tooltip>}>
                                <span>{formatDistanceToNow(new Date(repo.last_updated), { addSuffix: true })}</span>
                            </OverlayTrigger>
                        </Card.Text>
                    )}

                    {/* Description */}
                    {repo.desc && (
                        <Card.Text style={{ fontSize: '0.9rem' }}>
                            {repo.desc}
                        </Card.Text>
                    )}

                    <div className="d-flex">
                        {/* Download Count */}
                        {
                            <span className="align-items-center">
                                <i className="bi bi-download"></i>
                                <span> {repo.downloads}</span>
                            </span>
                        }

                        {/* Star Count */}
                        {
                            <div>
                                <i className="bi bi-dot" style={{ marginLeft: '0.2em', marginRight: '0.2em' }}></i>
                                <span className="align-items-center">
                                    <i className="bi bi-star"></i>
                                    <span> {repo.stars}</span>
                                </span>
                            </div>
                        }
                    </div>
                </Card.Body>
            </Card>
        </Col>
    );
};