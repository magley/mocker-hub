import { useNavigate, useParams } from "react-router-dom";
import "./OrgPage.css";
import { useEffect, useState } from "react";
import { OrganizationDTOBasic, OrganizationService } from "../api/org.api";
import { AxiosError, AxiosResponse } from "axios";
import { Nav, Spinner, Tab } from "react-bootstrap";
import { OrgMembers } from "../components/OrgMembers";
import { OrgRepositories } from "../components/OrgRepositories";
import { OrgTeams } from "../components/OrgTeams";

export const OrganizationPage = () => {
    const { "*": orgName } = useParams();
    const [loading, setLoading] = useState<boolean>(true);
    const [org, setOrg] = useState<OrganizationDTOBasic>();
    const [key, setKey] = useState<string>('members');
    const [amMemberOfOrg, setAmMemberOfOrg] = useState<boolean>(false);
    let navigate = useNavigate();

    useEffect(() => {
        fetchOrganizationByName(orgName!);
    }, []);

    const fetchOrganizationByName = (org_name: string) => {
        OrganizationService.FindByName(org_name).then((res: AxiosResponse<OrganizationDTOBasic>) => {
            setLoading(false);
            setOrg(res.data);

            fetchWhetherIamMemberOfOrg(res.data.id);
        }).catch((err: AxiosError) => {
            if (err.response?.status == 404) {
                navigate("/");
                console.error("Not found - either a typo or access denied.");
            } else {
                console.error(err);
            }
        });
    }

    const fetchWhetherIamMemberOfOrg = (org_id: number) => {
        OrganizationService.AmIMemberOfOrg(org_id).then((res) => {
            console.log(res.data);
            setAmMemberOfOrg(res.data.is_member);
        }).catch((err) => {
            console.error(err);
            setAmMemberOfOrg(false);
        });
    }

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    if (org) {
        return (
            <div className="org-page">
                {/* Organization Section */}
                <div className="org-page-header mb-4">
                    <h1>
                        {org?.name}
                    </h1>
                </div>

                {/* Tabs Section */}
                <Tab.Container activeKey={key} onSelect={(k) => setKey(k!)} id="tabs">
                    <Nav variant="tabs" className="mb-3">
                        <Nav.Item>
                            <Nav.Link eventKey="members" className={key === 'members' ? 'active' : ''}>
                                <i className="bi bi-person"> </i>
                                Members
                            </Nav.Link>
                        </Nav.Item>
                        <Nav.Item>
                            <Nav.Link eventKey="repositories" className={key === 'repositories' ? 'active' : ''}>
                                <i className="bi bi-boxes"> </i>
                                Repositories
                            </Nav.Link>
                        </Nav.Item>
                        {amMemberOfOrg && <Nav.Item>
                            <Nav.Link eventKey="teams" className={key === 'permissions' ? 'active' : ''}>
                                <i className="bi bi-people-fill"> </i>
                                Teams
                            </Nav.Link>
                        </Nav.Item>}
                    </Nav>

                    <Tab.Content>
                        <Tab.Pane eventKey="members">
                            <OrgMembers isActive={key === 'members'} />
                        </Tab.Pane>
                        <Tab.Pane eventKey="repositories">
                            <OrgRepositories isActive={key === 'repositories'} />
                        </Tab.Pane>
                        {amMemberOfOrg && <Tab.Pane eventKey="teams">
                            <OrgTeams isActive={key === 'teams'} org={org} />
                        </Tab.Pane>}
                    </Tab.Content>
                </Tab.Container>
            </div>
        );
    }
}