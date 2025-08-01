import React, { useEffect, useState } from "react";
import { Tab, Nav, Form, Button, Row, Col, Badge, Spinner, Alert } from "react-bootstrap";
import { OrgMembers } from "./OrgMembers";
import { TeamDTOBasic, TeamPermissionKind, TeamPermissionsDTO, TeamService } from "../api/team.api";
import { OrganizationDTOBasic } from "../api/org.api";
import { RepoDTO, RepositoryService } from "../api/repo.api";
import { AxiosError, AxiosResponse } from "axios";
import { getJwtId } from "../util/localstorage";
import { ToastType, useToastStore } from "../util/toastStore";


const permissionDescriptions: Record<TeamPermissionKind, string> = {
  [TeamPermissionKind.read]: "View repository info and pull tags.",
  [TeamPermissionKind.read_write]: "View repository info, push and pull tags.",
  [TeamPermissionKind.admin]: "Full access. Includes changing the description, visibility, deleting the repository and pushing/pulling tags",
};


export const TeamDetails: React.FC<{team: TeamDTOBasic, org: OrganizationDTOBasic; onBack: () => void;}> = ({ team, org, onBack }) => {
    const [tabKey, setTabKey] = useState("members");
    const [selectedRepoId, setSelectedRepoId] = useState<number | null>(null);
    const [selectedPermission, setSelectedPermission] = useState<TeamPermissionKind | "">("");
    const [repositories, setRepositories] = useState<RepoDTO[]>([]);
    const [teamPermissions, setTeamPermissions] = useState<TeamPermissionsDTO[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false); 
    const filteredRepos = repositories.filter(repo => !teamPermissions.some(tp => tp.repo_id === repo.id));

    const [editing, setEditing] = useState(false);
    const [editedName, setEditedName] = useState(team.name);
    const [editedDesc, setEditedDesc] = useState(team.desc || "");
    const [updating, setUpdating] = useState(false);
    const [error, setError] = useState('');
    const addToast = useToastStore((state) => state.addToast);


    useEffect(() => {
        checkIfIamOwnerOfOrg();
        fetchPermissions();
        fetchRepositories();
    }, []);

    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    }

    const fetchRepositories = async () => { 
        setLoading(true);
        RepositoryService.GetAllByOrganizationId(org.id).then((res: AxiosResponse<RepoDTO[]>) => {
            setRepositories(res.data);
        }).catch((err: AxiosError) => {
            console.error(err);
        }).finally(() => { 
            setLoading(false);
        })
    };

    const fetchPermissions = async () => {
        TeamService.GetPermissionsByTeamId(team.id).then((res: AxiosResponse<TeamPermissionsDTO[]>) => {
            setTeamPermissions(res.data || []);
        }).catch((err: AxiosError) => {
            console.error(err);
        });
    };

    const handleAddPermission = async () => {
        if (!selectedRepoId || !selectedPermission) return;
        setSubmitting(true);
        TeamService.AddPermission(team.id, selectedRepoId, selectedPermission as TeamPermissionKind).then(() => {
            fetchPermissions();
            setSelectedRepoId(null);
            setSelectedPermission("");
        }).catch((err: AxiosError) => {
            console.error(err);
        }).finally(() => {
            setSubmitting(false);
        });
    };

    const handleStartEdit = () => {
        setEditedName(team.name);
        setEditedDesc(team.desc || "");
        setEditing(true);
        setError('');
    };

    const handleCancelEdit = () => {
        setEditing(false);
        setError('');
    };

    const handleUpdateTeam = async () => {
        setUpdating(true);
        setError('');
        try {
            const res = await TeamService.UpdateTeam({...team, name: editedName.trim(), desc: editedDesc.trim()});
            team.name = res.data.name;
            team.desc = res.data.desc;
            setEditing(false);
            addToast(`Updated team name and description.`, ToastType.success);
        } catch (error: any) {
            console.error("Failed to update team:", error);
            setError(error["response"]["data"]["detail"]["message"]);
        } finally {
            setUpdating(false);
        }
    };

    return (
        <div className="p-4">
            {/* Header */}
            <div className="d-flex align-items-start mb-4" style={{ gap: "1.5rem" }}>
                <i className="bi bi-arrow-left" style={{ fontSize: "1.5rem", cursor: "pointer", marginTop: "6px" }} onClick={onBack}></i>

                {!editing ? (
                    <div>
                        <div className="d-flex align-items-center">
                            <h2 className="m-0 me-2">{team.name}</h2>
                            {amOwnerOfOrg && (
                                <button className="btn btn-link p-0" onClick={handleStartEdit}>
                                    <i className="bi bi-pencil" style={{ marginLeft: "5px" }}></i>
                                </button>
                            )}
                        </div>
                        {team.desc && <p className="text-muted mb-0 mt-1">{team.desc}</p>}
                    </div>
                ) : (
                    <div style={{ maxWidth: "600px", width: "100%" }}>
                        <Form.Group className="mb-3">
                            <Form.Label className="bold">Team Name</Form.Label>
                            <Form.Control value={editedName} onChange={(e) => setEditedName(e.target.value)} placeholder="Team name" />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label className="bold">Team Description</Form.Label>
                            <Form.Control as="textarea" rows={2} value={editedDesc} onChange={(e) => setEditedDesc(e.target.value)} placeholder="Team description" />
                        </Form.Group>
                        <div>
                            <Button variant="primary" disabled={updating} onClick={handleUpdateTeam}>{updating ? "Updating..." : "Update"}</Button>
                            <Button variant="secondary" className="me-2" onClick={handleCancelEdit}>Cancel</Button>
                        </div>
                    </div>
                )}
            </div>
            {error && <Alert variant="danger">{error}</Alert>}

            {/* Tabs */}
            <Tab.Container activeKey={tabKey} onSelect={(k) => setTabKey(k || "members")}>
                <Nav variant="tabs" className="mb-3">
                    <Nav.Item>
                        <Nav.Link eventKey="members" className={tabKey === "members" ? "active" : ""}>
                            <i className="bi bi-person"> </i> Members
                        </Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                        <Nav.Link eventKey="permissions" className={tabKey === "permissions" ? "active" : ""}>
                            <i className="bi bi-shield-lock"> </i> Permissions
                        </Nav.Link>
                    </Nav.Item>
                </Nav>

                <Tab.Content>
                    <Tab.Pane eventKey="members">
                        <OrgMembers isActive={tabKey === "members"} org={org} teamId={team.id} />
                    </Tab.Pane>

                    <Tab.Pane eventKey="permissions">
                        {loading ? (
                            <div className="text-center my-4">
                                <Spinner animation="border" />
                            </div>
                        ) : (
                            <>
                                <div className="mb-3" style={{maxWidth: "70%"}}>
                                    {amOwnerOfOrg && (
                                    <Row className="align-items-end mb-3">
                                        <Col md={5}>
                                            <Form.Group controlId="repositorySelect">
                                                <Form.Select
                                                    value={selectedRepoId ?? ""}
                                                    onChange={(e) => setSelectedRepoId(Number(e.target.value))}
                                                    >
                                                    <option value="" disabled hidden>Select repository</option>
                                                    {filteredRepos.map((repo) => (
                                                        <option key={repo.id} value={repo.id}>
                                                        {repo.name}
                                                        </option>
                                                    ))}
                                                    </Form.Select>
                                            </Form.Group>
                                        </Col>
                                        <Col md={4}>
                                            <Form.Group controlId="permissionSelect">
                                                <Form.Select
                                                    value={selectedPermission}
                                                    onChange={(e) => setSelectedPermission(e.target.value as TeamPermissionKind | "")}
                                                    >
                                                    <option value="" disabled hidden>Select permission</option>
                                                    {Object.values(TeamPermissionKind).map((perm) => (
                                                        <option key={perm} value={perm}>
                                                        {perm.charAt(0).toUpperCase() + perm.slice(1).replace("_", " ")}
                                                        </option>
                                                    ))}
                                                    </Form.Select>

                                            </Form.Group>
                                        </Col>
                                        <Col md={3}>
                                            <Button
                                                variant="primary"
                                                disabled={!selectedRepoId || !selectedPermission || submitting}
                                                onClick={handleAddPermission}
                                            >
                                                {submitting ? "Adding..." : "Add"}
                                            </Button>
                                        </Col>
                                    </Row>
                                    )}

                                    {selectedPermission && (
                                        <div className="mb-3">
                                            <small className="text-muted">
                                                <strong>Description:</strong>{" "}
                                                {permissionDescriptions[selectedPermission]}
                                            </small>
                                        </div>
                                        )}
                                    {teamPermissions.length === 0 ? (
                                        <p>No permissions assigned yet.</p>
                                            ) : (
                                            <div className="mt-4">
                                                <Row className="fw-bold mb-2">
                                                </Row>
                                                {teamPermissions.map((item, index) => {
                                                const repo = repositories.find((r) => r.id === item.repo_id);
                                                return (
                                                    <Row key={index} className="align-items-start border rounded p-2 mb-2 hover-shadow">
                                                    <Col md={5}>
                                                        <div className="fw-semibold">{repo?.name || "Unknown repository"}</div>
                                                    </Col>
                                                    <Col md={7}>
                                                        <Badge bg="secondary" className="text-uppercase mb-1">
                                                        {item.kind}
                                                        </Badge>
                                                        <div className="text-muted small">
                                                        {permissionDescriptions[item.kind]}
                                                        </div>
                                                    </Col>
                                                    </Row>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </>
                        )}
                    </Tab.Pane>
                </Tab.Content>
            </Tab.Container>
        </div>
    );
};
