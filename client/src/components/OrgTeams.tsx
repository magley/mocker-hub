import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic } from "../api/org.api";
import { TeamCreateDTO, TeamDTOBasic, TeamService } from "../api/team.api";
import { AxiosError, AxiosResponse } from "axios";
import { Button, Form, Modal, Spinner } from "react-bootstrap";
import { getJwtId } from "../util/localstorage";
import "./OrgTeams.css";

export const OrgTeams: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
    const [teams, setTeams] = useState<TeamDTOBasic[]>([]);
    const [loading, setLoading] = useState(true);
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false);

    // -------------------------------------------
    // Modal window properties.
    //
    const [showModal, setShowModal] = useState(false);
    const [teamName, setTeamName] = useState('');
    const [teamDescription, setTeamDescription] = useState('');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleClose = () => {
        setShowModal(false);
        setTeamName('');
        setTeamDescription('');
    }
    const handleShow = () => setShowModal(true);

    const handleSubmit = (event: React.FormEvent) => {
        event.preventDefault();

        const data: TeamCreateDTO = {
            name: teamName,
            organization_id: org.id
        }

        setErrorMessage(null);

        TeamService.Create(data).then((res) => {
            setTeams([...teams, res.data]); // This is a good reason not not extract the modal window into a child component.
            handleClose();
        }).catch((err: AxiosError) => {
            setErrorMessage((err.response?.data as any)["detail"]["message"]);
        });
    };
    //
    // -------------------------------------------


    useEffect(() => {
        if (isActive) {
            getTeams();
            checkIfIamOwnerOfOrg();
        }
    }, [isActive]);

    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    }

    const getTeams = () => {
        setLoading(true);
        setTeams([]);

        TeamService.FindByOrganizationId(org.id).then((res: AxiosResponse<TeamDTOBasic[]>) => {
            setTeams(res.data);
        }).catch((err: AxiosError) => {
            console.error(err);
        }).finally(() => {
            setLoading(false);
        })
    }

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    return (
        <>
            {/* No teams */}

            {teams.length == 0 && (<>
                <h1 className="no-teams-text">This organization does not have teams.</h1>
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-center">
                        <Button variant="primary" onClick={handleShow}>New Team</Button>
                    </div>
                )}
            </>)}

            {/* Yes teams */}

            {teams.length > 0 && (<>
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-center">
                        <Button variant="primary" onClick={handleShow}>New Team</Button>
                    </div>
                )}

                {teams.length > 0 && (teams.map((team, i) => (
                    <div key={i}>{team.name} (TODO - View add and remove members)</div>
                )))}
            </>)}

            {/* Modal form - create a team. */}

            <Modal
                show={showModal}
                onHide={handleClose}
                backdrop="static"
                keyboard={false}
                centered
                size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Create a Team</Modal.Title>
                </Modal.Header>
                <Modal.Body className="p-4">
                    {/* Form inside modal */}
                    <Form onSubmit={handleSubmit}>
                        <Form.Group controlId="teamName" className="mb-3">
                            <Form.Label className="mb-2">Team Name</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Enter team name"
                                value={teamName}
                                onChange={(e) => setTeamName(e.target.value)}
                                required
                            />
                        </Form.Group>

                        <Form.Group controlId="teamDescription" className="mb-3">
                            <Form.Label className="mb-2">Team Description (Optional)</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Enter team description"
                                value={teamDescription}
                                onChange={(e) => setTeamDescription(e.target.value)}
                            />
                        </Form.Group>

                        {/* Error message */}
                        {errorMessage && (
                            <div className="text-danger mb-3">
                                {errorMessage}
                            </div>
                        )}

                        <div className="d-flex justify-content-between">
                            <Button variant="secondary" onClick={handleClose} className="mr-2">
                                Cancel
                            </Button>
                            <Button variant="primary" type="submit">
                                Submit
                            </Button>
                        </div>
                    </Form>
                </Modal.Body>
            </Modal>
        </>
    );
}