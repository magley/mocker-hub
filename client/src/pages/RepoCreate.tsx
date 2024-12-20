import { useEffect, useState } from 'react';
import { Form, Button, DropdownButton, Dropdown, Col, Row, Alert } from 'react-bootstrap';
import './RepoCreate.css';
import { RepoCreateDTO, RepoDTO, RepositoryService } from '../api/repo.api';
import { AxiosError, AxiosResponse } from 'axios';
import { getJwtId } from '../util/localstorage';
import { OrganizationDTOBasic, OrganizationService } from '../api/org.api';

interface Owner {
    name: string;
    user_id: number | null;
    organization_id: number | null;
}

export const RepoCreate = () => {
    const [name, setName] = useState('');
    const [owner, setOwner] = useState<Owner | null>(null);
    const [description, setDescription] = useState('');
    const [isPublic, setIsPublic] = useState(true);
    const [owners, setOwners] = useState<Owner[]>([]);
    const [error, setError] = useState('');

    useEffect(() => {
        // Fetch all organizations this user can create repositories in.

        OrganizationService.GetMyOrganizations().then((res: AxiosResponse<OrganizationDTOBasic[]>) => {
            const orgs = res.data;

            // TODO: Improve access control. Right now, any member of the organization
            // can add repositories to that organization. We may want to restrict that.
            const organizations_i_can_make_repos_in: Owner[] = orgs.map(o => {
                return {
                    name: o.name,
                    user_id: null,
                    organization_id: o.id
                };
            });

            // Create list of "owners" (the user himself + all the organizations above).

            const all_possible_owners = [
                { name: "user 1", user_id: getJwtId(), organization_id: null },
                ...organizations_i_can_make_repos_in
            ]
            setOwners(all_possible_owners);

            // The inital value of the dropdown list is the user.
            //
            // NOTE: I use `all_possible_owners[0]` instead of `owners[0]`
            // because `owners` may have not been updated by the setOwners
            // above. This is because state is async, so at this point `owners`
            // may still not be updated (i.e. it's still empty).
            setOwner(all_possible_owners[0]);
        }).catch((err: AxiosError) => {
            setError("Failed to fetch organizations that I am a member of. Check your console.");
            console.error(err);
        });

    }, []);

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

        setError('');
        RepositoryService.CreateRepository(dto).then((res) => {
            let repo: RepoDTO = res.data;
            console.log(repo);
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

    return (
        <Form onSubmit={handleSubmit} className="repo-create">
            <h1>Create a new repository</h1>

            <Row>
                <Col xs="auto">
                    <Form.Group controlId="formOwner">
                        <Form.Label>Owner</Form.Label>
                        <DropdownButton
                            id="dropdown-owner"
                            title={owner ? `${userOrOrgToStr(owner)}` : 'Select Owner'}
                            onSelect={(eventKey) => {
                                const selectedOwner = owners.find((o) => o.name === eventKey);
                                setOwner(selectedOwner || null);
                            }}
                        >
                            {owners.map((o) => (
                                <Dropdown.Item key={o.name} eventKey={o.name}>
                                    {userOrOrgToStr(o)}
                                </Dropdown.Item>
                            ))}
                        </DropdownButton>
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
                    Create Repository
                </Button>
            </div>
        </Form>
    );
};