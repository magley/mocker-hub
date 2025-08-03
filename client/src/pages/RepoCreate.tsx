import { useEffect, useState } from 'react';
import { Form, Button, DropdownButton, Dropdown, Col, Row, Alert, Spinner } from 'react-bootstrap';
import './RepoCreate.css';
import { RepoCreateDTO, RepoDTO, RepositoryService } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import { getJwtId } from '../util/localstorage';
import { OrganizationDTOBasic, OrganizationService } from '../api/org.api';
import { useNavigate } from 'react-router-dom';
import { ToastType, useToastStore } from '../util/toastStore';
import { useParams } from 'react-router-dom';
import Select from 'react-select';

interface Owner {
    name: string;
    user_id: number | null;
    organization_id: number | null;
    image_path: string | null;
}

export const RepoCreate = () => {
    const [name, setName] = useState('');
    const [owner, setOwner] = useState<Owner | null>(null);
    const [description, setDescription] = useState('');
    const [isPublic, setIsPublic] = useState(true);
    const [owners, setOwners] = useState<Owner[]>([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const addToast = useToastStore((state) => state.addToast);

    const { orgId } = useParams<{ orgId?: string }>();


    useEffect(() => {
    OrganizationService.GetMyOrganizations().then((res: AxiosResponse<OrganizationDTOBasic[]>) => {
        const orgs = res.data;

        const organizations_i_can_make_repos_in: Owner[] = orgs.map(o => ({
            name: o.name,
            user_id: null,
            organization_id: o.id,
            image_path: o.image,
        }));

        const currentUser: Owner = {
            name: "User",
            user_id: getJwtId(),
            organization_id: null,
            image_path: null,
        };

        const all_possible_owners: Owner[] = [currentUser, ...organizations_i_can_make_repos_in];
        setOwners(all_possible_owners);

        // Auto-select the org if `orgId` is provided and matches an org
        let selected: Owner | undefined;
        if (orgId) {
            const parsedOrgId = parseInt(orgId);
            selected = all_possible_owners.find(o => o.organization_id === parsedOrgId);
        }

        setOwner(selected || currentUser);

    }).catch((err: AxiosError) => {
        setError("Failed to fetch organizations that I am a member of. Check your console.");
        console.error(err);
    });
}, [orgId]);


    const userOrOrgToStr = (owner: Owner) => {
        if (owner.user_id != null) {
            return `${owner.name} (You)`;
        }
        if (owner.organization_id != null) {
            return `${owner.name} (Organization)`;
        }
        console.error(`Bad owner object: ${owner}`);
        return "";
    }

    const handleSubmit = (event: React.FormEvent) => {
        event.preventDefault();
        const data = {
            name,
            owner,
            description,
            isPublic,
        };

        if (!owner) {
            setError("Please select the owner of this repository.");
            return;
        }

        if (!data.name.trim()) {
            setError("Please enter the name of the repository.");
            return;
        }

        if (!owners[0].user_id) {
            setError("First owner in owners does not have user_id set. Check the console.");
            console.error("The first element of owners should represent the currently signed in user. Its user_id should match the one from the JWT.");
            console.error(owners);
            return;
        }


        let dto: RepoCreateDTO = {
            desc: data.description,
            name: data.name,
            public: data.isPublic,
            organization_id: owner!.organization_id,
        };

        setLoading(true);
        setError('');
        RepositoryService.CreateRepository(dto).then((res) => {
            let repo: RepoDTO = res.data;

            addToast(`Created repository ${repo.name}`, ToastType.success);
            navigate(`/r/${repo.canonical_name}`);
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        }).finally(() => {
            setLoading(false);
        });
    };

    const options = owners.map((owner) => ({
        value: owner.name,
        label: (
            <div style={{ display: 'flex', alignItems: 'center' }}>
            {owner.image_path && (
                <img
                src={OrganizationService.GetImageURI(owner.image_path)}
                alt=""
                style={{ width: 30, height: 30, borderRadius: '50%', marginRight: 10 }}
                />
            )}
            {userOrOrgToStr(owner)}
            </div>
        ),
        data: owner, // Keep original owner object for later use
    }));

    const selectedOption = options.find((o) => o.data.name === owner?.name);

    return (
        <Form onSubmit={handleSubmit} className="repo-create">
            <h1>Create a new repository</h1>

            <Row>
                <Col xs="auto">
                    <Form.Group controlId="formOwner" className='owner-select'>
                        <Form.Label>Owner</Form.Label>
                        <Select
                            options={options}
                            value={selectedOption}
                            onChange={(selected) => {
                            if (selected) {
                                setOwner((selected as any).data);
                            }
                            }}
                            isSearchable={false}
                            className='owner-select'
                        />
                    </Form.Group>
                </Col>
                <Col>
                    <Form.Group controlId="formName">
                        <Form.Label>Name</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Enter repository name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </Form.Group>
                </Col>
            </Row>

            <Form.Group controlId="formDescription" className='desc-formgroup'>
                <Form.Label>Description (Optional)</Form.Label>
                <Form.Control
                    as="textarea"
                    rows={3}
                    placeholder=""
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />
            </Form.Group>

            <Form.Group controlId="formPublic" className='is-public-radiogroup'>
                <div>
                    <Form.Check
                        type="radio"
                        label={<><i className="bi bi-journal-bookmark"></i> <b>Public</b> - Anyone can see and pull from this repository</>}
                        name="visibility"
                        id="visibility-radio-public"
                        checked={isPublic}
                        onChange={() => setIsPublic(true)}
                    />
                    <Form.Check
                        type="radio"
                        label={<><i className="bi bi-lock"></i> <b>Private</b> - Only you have access to this repository</>}
                        name="visibility"
                        id="visibility-radio-private"
                        checked={!isPublic}
                        onChange={() => setIsPublic(false)}
                    />
                </div>
            </Form.Group>

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="d-flex justify-content-end">
                <Button variant="primary" type="submit">
                    {loading && (
                        <Spinner
                            as="span"
                            size="sm"
                            role="status"
                            aria-hidden="true"
                        > </Spinner>
                    )}
                    Create Repository
                </Button>
            </div>
        </Form>
    );
};