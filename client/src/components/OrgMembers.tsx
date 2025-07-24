import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic, OrganizationService } from "../api/org.api";
import { UserDTO, UserService } from "../api/user.api";
import { AxiosError, AxiosResponse } from "axios";
import { Button, Form, ListGroup, Modal, Spinner } from "react-bootstrap";
import { getJwtId } from "../util/localstorage";

export const OrgMembers: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
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

        OrganizationService.GetMembersOfOrg(org.id).then((res: AxiosResponse<UserDTO[]>) => {
            setMembers(res.data);
        }).catch((err: AxiosError) => {
            console.error(err);
        }).finally(() => {
            setLoading(false);
        })
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

        try {
            const res: AxiosResponse<UserDTO[]> = await UserService.SearchUsers(query, org.id);
            setSearchResults(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setSearchLoading(false);
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
    };
    
    const handleAddMembers = async () => {
        if (selectedUsers.length === 0) return;

        try {
            await OrganizationService.AddUsersToOrg(org.id, selectedUsers.map((u) => u.id));
            getMembers(); 
            handleClose();
        } catch (err) {
            console.error("Failed to add members", err);
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
                <h1 className="no-teams-text">This organization does not have any members.</h1>
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
                        <div className="d-flex justify-content-center mb-3">
                            <Button variant="primary" onClick={handleShow}>
                                Add Members
                            </Button>
                        </div>
                    )}

                    {members.map((member, i) => (
                        <div key={i}>{member.username} </div>
                    ))}
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
                            {searchResults.map((user) => {
                                const isSelected = selectedUsers.find((u) => u.id === user.id);
                                return (
                                    <ListGroup.Item
                                        key={user.id}
                                        action
                                        active={!!isSelected}
                                        onClick={() => toggleSelectUser(user)}
                                    >
                                        {user.username} ({user.email})
                                    </ListGroup.Item>
                                );
                            })}
                        </ListGroup>
                    )}

                    {selectedUsers.length > 0 && (
                        <div className="mt-3">
                            <strong>Selected users:</strong>{" "}
                            {selectedUsers.map((u) => u.username).join(", ")}
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