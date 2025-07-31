import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic } from "../api/org.api";
import { TeamCreateDTO, TeamDTOBasic, TeamService } from "../api/team.api";
import { AxiosError, AxiosResponse } from "axios";
import { Button, Form, Modal, Spinner } from "react-bootstrap";
import { getJwtId } from "../util/localstorage";
import "./OrgTeams.css";
import { TeamDetails } from "./TeamDetails";

export const OrgTeams: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
    const [teams, setTeams] = useState<TeamDTOBasic[]>([]);
    const [loading, setLoading] = useState(true);
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false);
    const [selectedTeam, setSelectedTeam] = useState<TeamDTOBasic | null>(null);


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
            desc: teamDescription,
            organization_id: org.id
        }

        setErrorMessage(null);

        TeamService.Create(data).then((res) => {
            getTeams();
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
        {selectedTeam ? (
            <TeamDetails team={selectedTeam} org={org} onBack={() => setSelectedTeam(null)} />
        ) : (
            <>
            {/* No teams */}
            {teams.length == 0 && (<>
                <h1 className="no-teams-text">This organization does not have teams.</h1>
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-end mb-3 ms-4" style={{maxWidth:"58%"}}>
                        <Button variant="primary" onClick={handleShow}>Create Team</Button>
                    </div>
                )}
            </>)}

            {/* Yes teams */}
            {teams.length > 0 && (<>
                {amOwnerOfOrg && (
                    <div className="d-flex justify-content-end mb-3 ms-4" style={{maxWidth:"58%"}}>
                        <Button variant="primary" onClick={handleShow}>Create Team</Button>
                    </div>
                )}

                <div className="ms-4 me-5 mt-5" style={{ maxWidth: "85%" }}>

                        {/* Table Header */}
                        <div
                            className="d-flex fw-bold border-bottom pb-3"
                            style={{ fontSize: "1.05rem", letterSpacing: "0.3px", maxWidth: "70%" }}
                        >
                            <div style={{ width: "30%", paddingLeft: "8px" }}>Team name</div>
                            <div style={{ width: "50%" }}>Description</div>
                            <div style={{ width: "20%" }}>Members</div>
                        </div>

                        {/* Table Rows */}
                        {teams.map((team) => {
                            return (
                            <div key={team.id} className="d-flex align-items-center border-bottom team-row"
                                style={{ fontSize: "1rem", padding: "12px 0", maxWidth: "70%", cursor: "pointer" }}
                                onClick={() => setSelectedTeam(team)}>

                                <div style={{ width: "30%", paddingLeft: "8px" }} className="fw-bold">
                                    {team.name}
                                </div>

                                <div style={{ width: "50%", paddingLeft: "4px" }} className="text-muted">
                                    {team.desc}
                                </div>  
 
                                <div style={{ width: "20%", paddingLeft: "30px"}} className="text-dark">
                                    {team.members_count}
                                </div>
                            </div>
                            );
                        })}
                 </div>
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
        )}
    </>
    );
}
