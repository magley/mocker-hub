import React, { useState } from "react";
import { Tab, Nav } from "react-bootstrap";
import "./OrgTeams.css"; // You can add styling here

interface TeamDetailsProps {
    team: {
        name: string;
        desc?: string;
    };
    onBack: () => void;
}

export const TeamDetails: React.FC<TeamDetailsProps> = ({ team, onBack }) => {
    const [tabKey, setTabKey] = useState("members");

    return (
        <div className="p-4">

            {/* Header */}
            <div className="d-flex align-items-center mb-4" style={{ gap: "12px" }}>
                <i
                    className="bi bi-arrow-left"
                    style={{ fontSize: "1.5rem", cursor: "pointer" }}
                    onClick={onBack}
                ></i>
                <div>
                    <h2 className="m-0">{team.name}</h2>
                    {team.desc && <p className="text-muted mb-0">{team.desc}</p>}
                </div>
            </div>

            {/* Tabs */}
            <Tab.Container activeKey={tabKey} onSelect={(k) => setTabKey(k || "members")}>
                <Nav variant="tabs" className="mb-3">
                    <Nav.Item>
                        <Nav.Link eventKey="members" className={tabKey === "members" ? "active" : ""}>
                            <i className="bi bi-person"> </i>
                            Members
                        </Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                        <Nav.Link eventKey="permissions" className={tabKey === "permissions" ? "active" : ""}>
                            <i className="bi bi-shield-lock"> </i>
                            Permissions
                        </Nav.Link>
                    </Nav.Item>
                </Nav>

                <Tab.Content>
                    <Tab.Pane eventKey="members">
                        {/* Placeholder members content */}
                        <p>This is the <strong>Members</strong> tab content. List team members here.</p>
                    </Tab.Pane>

                    <Tab.Pane eventKey="permissions">
                        {/* Placeholder permissions content */}
                        <p>This is the <strong>Permissions</strong> tab content. Show permission roles here.</p>
                    </Tab.Pane>
                </Tab.Content>
            </Tab.Container>
        </div>
    );
};
