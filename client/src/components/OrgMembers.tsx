import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic, OrganizationService } from "../api/org.api";
import { UserDTO, UserService } from "../api/user.api";
import { AxiosError, AxiosResponse } from "axios";
import { Badge, Button, Form, ListGroup, Modal, Spinner } from "react-bootstrap";
import { getJwtId } from "../util/localstorage";
import "./OrgMembers.css";
import { Link } from "react-router-dom";
import { TeamService } from "../api/team.api";

export const OrgMembers: React.FC<{ isActive: boolean, org: OrganizationDTOBasic, teamId : number | null }> = ({ isActive, org, teamId = -1 }) => {
    const [members, setMembers] = useState<UserDTO[]>([]);
    const [loading, setLoading] = useState(true);
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false); 

    const [showModal, setShowModal] = useState(false);
    
    const [searchTerm, setSearchTerm] = useState("");
    const [searchResults, setSearchResults] = useState<UserDTO[]>([]);
    const [selectedUsers, setSelectedUsers] = useState<UserDTO[]>([]);
    const [searchLoading, setSearchLoading] = useState(false);

    useEffect(() => {
        if (isActive) { 
            getMembers();
            checkIfIamOwnerOfOrg();
        }
    }, [isActive]);

    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    }

    const getMembers = () => {
        setLoading(true);
        setMembers([]);

        if (teamId === null || teamId === -1) {
            OrganizationService.GetMembersOfOrg(org.id).then((res: AxiosResponse<UserDTO[]>) => {
                setMembers(res.data);
            }).catch((err: AxiosError) => {
                console.error(err);
            }).finally(() => { 
                setLoading(false);
            })
        } else { 
            TeamService.GetMembersOfTeam(teamId).then((res: AxiosResponse<UserDTO[]>) => {
                setMembers(res.data);
            }).catch((err: AxiosError) => {
                console.error(err);
            }).finally(() => {
                setLoading(false);
            })
        }
    }

    const handleClose = () => {
        setShowModal(false);
        setSearchTerm("");
        setSearchResults([]);
        setSelectedUsers([]);
    };

    const handleShow = () => setShowModal(true);

    const searchUsers = async (query: string) => {
        if (!query.trim()) {
            setSearchResults([]);
            return;
        }
        setSearchLoading(true);

        if ((teamId === null || teamId === -1)) {
            try {
                const res: AxiosResponse<UserDTO[]> = await UserService.SearchUsers(query, org.id);
                setSearchResults(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setSearchLoading(false);
            }
        } else{
            try {
                const res: AxiosResponse<UserDTO[]> = await OrganizationService.SearchMembers(query, teamId);
                setSearchResults(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setSearchLoading(false);
            }
        }
    };

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSearchTerm(value);
        searchUsers(value);
    };

    const toggleSelectUser = (user: UserDTO) => {
        if (selectedUsers.find((u) => u.id === user.id)) {
            setSelectedUsers(selectedUsers.filter((u) => u.id !== user.id));
        } else {
            setSelectedUsers([...selectedUsers, user]);
        }

        setSearchTerm("");
        setSearchResults([]);
    };
    
    const handleAddMembers = async () => {
        if (selectedUsers.length === 0) return;

        if ((teamId === null || teamId === -1)) {
            try {
                await OrganizationService.AddUsersToOrg(org.id, selectedUsers.map((u) => u.id));
                getMembers(); 
                handleClose();
            } catch (err) {
                console.error("Failed to add members", err);
            }
        }  else{
            try {
                await TeamService.AddMembersToTeam(teamId, selectedUsers.map((u) => u.id));
                getMembers(); 
                handleClose();
            } catch (err) {
                console.error("Failed to add members", err);
            }
        }
    };

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    return (
        <>
            {/* No members */}
            {members.length == 0 && (<>
                {(teamId === null || teamId === -1) && <h1 className="no-teams-text">This organization does not have any members.</h1>}
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-center">
                        <Button variant="primary" onClick={handleShow}>Add Members</Button>
                    </div>
                )}
            </>)}

            {/* Has members */}
            {members.length > 0 && (
                <>
                    {amOwnerOfOrg && (
                        <div className="d-flex justify-content-end mb-3 ms-4" style={{maxWidth:"75%"}}>
                            <Button variant="primary" onClick={handleShow}>
                                Add Members
                            </Button>
                        </div>
                    )}

                    <div className="ms-4 me-5" style={{ maxWidth: "85%", marginBottom: "1.5rem" }}>

                        {/* Table Header */}
                        <div
                            className="d-flex fw-bold border-bottom pb-3"
                            style={{ fontSize: "1.05rem", letterSpacing: "0.3px", maxWidth: "90%" }}
                        >
                            <div style={{ width: "20%", paddingLeft: "8px" }}>Username</div>
                            <div style={{ width: "25%" }}>Full Name</div>
                            <div style={{ width: "35%" }}>Email</div>
                            {(teamId === null || teamId === -1) && <div style={{ width: "10%" }}>Role</div>}
                        </div>

                        {/* Table Rows */}
                        {members.map((member) => {
                            const isOwner = member.id === org.owner_id;

                            return (
                            <div
                                key={member.id} className="d-flex align-items-center border-bottom"
                                style={{fontSize: "1rem",padding: "12px 0", maxWidth: "90%"}}
                                >
                                    
                                <div style={{ width: "20%", paddingLeft: "8px"}}>
                                <Link to={`/u/${member.username}`} className="fw-bold text-primary" 
                                      style={{ textDecoration: "none", cursor: "pointer" }}>
                                    {member.username}
                                </Link>
                                </div>

                                <div style={{ width: "25%" }} className="text-muted">
                                {member.first_name} {member.last_name}
                                </div>

                                <div style={{ width: "35%" }} className="text-dark">
                                <i className="bi bi-envelope me-1 text-secondary"></i> {member.email || "—"}
                                </div>

                                {(teamId === null || teamId === -1) && <div style={{ width: "10%" }}>
                                    {isOwner ? (<Badge className="custom-owner-badge">Owner</Badge>) : (
                                        <Badge className="custom-member-badge">Member</Badge>
                                    )}
                                    </div>
                                }
                            </div>
                            );
                        })}
                    </div>
                </>
            )}

            {/* Modal for inviting members */}
            <Modal show={showModal} onHide={handleClose} backdrop="static" centered size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Add Members</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form.Group className="mb-3">
                        <Form.Label>Search users by username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Type to search..."
                            value={searchTerm}
                            onChange={handleSearchChange}
                        />
                    </Form.Group>

                    {searchLoading && <Spinner animation="border" size="sm" />}

                    {searchResults.length > 0 && (
                        <ListGroup>
                            {searchResults.filter((user) => !selectedUsers.some((u) => u.id === user.id)).map((user) => (
                                <ListGroup.Item key={user.id} action onClick={() => toggleSelectUser(user)}>
                                {user.username} ({user.email})
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                    )}

                    {selectedUsers.length > 0 && (
                        <div className="mt-3">
                            <strong>Selected users:</strong>
                            <div className="mt-2 d-flex flex-wrap gap-2">
                            {selectedUsers.map((u) => (
                                <span key={u.id} className="chip badge bg-primary text-white d-flex align-items-center"
                                style={{
                                    fontSize: "0.9rem",
                                    padding: "0.5em 0.8em",
                                    borderRadius: "20px",
                                    cursor: "pointer",
                                }} onClick={() => setSelectedUsers(selectedUsers.filter((usr) => usr.id !== u.id))}>
                                    {u.username}
                                <i className="bi bi-x-circle ms-2"></i>
                                </span>
                            ))}
                        </div>
                    </div>
                    )}

                    <div className="d-flex justify-content-between mt-3">
                        <Button variant="secondary" onClick={handleClose} className="mr-2">
                            Cancel
                        </Button>
                        <Button variant="primary" onClick={handleAddMembers} disabled={selectedUsers.length === 0}>
                            Add Selected Users
                        </Button>
                    </div>
                </Modal.Body>
            </Modal>
        </>
    );
}