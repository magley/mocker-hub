import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Button, Row, Spinner } from 'react-bootstrap';
import { OrganizationDTOBasic, OrganizationService } from '../api/org.api';
import { AxiosError, AxiosResponse } from 'axios';
import './OrgOfUser.css';
import { OrgPreview } from '../components/OrgPreview';

export const OrganisationsOfUser: React.FC = () => {
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const { username } = useParams<{ username: string }>();

    const [organisations, setOrganisations] = useState<OrganizationDTOBasic[]>([]);
    const [filteredOrgs, setFilteredOrgs] = useState<OrganizationDTOBasic[]>([]);

    const [searchTerm, setSearchTerm] = useState('');

    let navigate = useNavigate();

    useEffect(() => {
        fetchOrgs();
    }, []);

    const fetchOrgs = () => {
        if (username === undefined) {
            navigate(`/`);
            return;
        }

        OrganizationService.GetMyOrganizations().then((res: AxiosResponse<OrganizationDTOBasic[]>) => {
            setLoading(false);
            setOrganisations(res.data);
            setFilteredOrgs(res.data);

        }).catch((err: AxiosError) => {
            setLoading(false);
            setError((err.response?.data as any)["detail"]["message"]);
        })
    }

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        filterOrgs(e.target.value);
    };

    const filterOrgs = (searchTerm: string) => {
        let filtered = organisations.filter((org) => {
            const matchesSearch =
                org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (org.desc && org.desc.toLowerCase().includes(searchTerm.toLowerCase()));
            return matchesSearch;
        });
        setFilteredOrgs(filtered);
    };

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center">
                <Spinner animation="border" />
            </div>
        );
    }

    if (error) {
        return <div className="alert alert-danger">{error}</div>;
    }

    return (
        <Row className="g-4 org-of-user">
            {/* Page Title */}
            {<h1>Organisations</h1> }

            { organisations!.length >= 1 ? (
                <>
                <div className="d-flex justify-content-between">
                    <div className="d-flex align-items-center flex-grow-1 me-3" style={{ maxWidth: "70%" }}>
                        {/* Search Bar */}
                        <input
                            type="text"
                            className="form-control me-2"
                            placeholder="Search organisations"
                            value={searchTerm}
                            onChange={handleSearchChange}
                        />
                    </div>
                    
                    {/* Add new organisation Button */}
                    <Link to={`/org`}>
                        <Button className="btn btn-primary">
                                Create Organisation
                        </Button>
                    </Link>
                </div>
                {
                    filteredOrgs.map((org) => (
                        <OrgPreview key={org.id} org={org} />
                    ))
                }
                </>
            ) : ( <div>No organisations that you are a part of.</div> ) }

        </Row>
    );
};