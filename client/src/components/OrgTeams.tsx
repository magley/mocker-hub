import React, { useEffect, useState } from "react";
import { OrganizationDTOBasic } from "../api/org.api";
import { TeamDTOBasic, TeamService } from "../api/team.api";
import { AxiosError, AxiosResponse } from "axios";
import { Spinner } from "react-bootstrap";

export const OrgTeams: React.FC<{ isActive: boolean, org: OrganizationDTOBasic }> = ({ isActive, org }) => {
    const [teams, setTeams] = useState<TeamDTOBasic[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isActive) {
            getTeams();
        }
    }, [isActive]);

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
            {teams.map((team, _) => (
                <div>{team.name} (TODO - View add and remove members)</div>
            ))}
        </>
    );
}