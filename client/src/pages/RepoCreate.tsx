import { useEffect, useState } from 'react';
import { Form, Button, DropdownButton, Dropdown, Col, Row, Alert } from 'react-bootstrap';
import './RepoCreate.css';
import { RepoCreateDTO, RepoDTO, RepositoryService } from '../api/repo.api';
import { AxiosError } from 'axios';

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

        // TODO: Axios fetch organizations for the user.
        const organizations_i_can_make_repos_in: Owner[] = [
            { name: "org 1", user_id: null, organization_id: 1 },
            { name: "org 2", user_id: null, organization_id: 2 },
        ];

        const all_possible_owners = [
            { name: "user 1", user_id: 1, organization_id: null },
            ...organizations_i_can_make_repos_in
        ]

        // Create list of "owners" (the user himself + all the organizations above).

        setOwners(all_possible_owners);

        // The inital value of the dropdown list is the user.

        // NOTE: I use `all_possible_owners[0]` instead of `owners[0]` because `owners`
        // may have not updated yet. This is because state is async and `owners` will update
        // on the next render, so this will fail. 
        setOwner(all_possible_owners[0]);
    }, []);

    const userOrOrgToStr = (owner: Owner) => {
        if (owner.user_id != null) {
            return `User ${owner.user_id} (You)`;
        }
        if (owner.organization_id != null) {
            return `Organization ${owner.organization_id}`;
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

            owner_id: owners[0].user_id!,
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
                        checked={isPublic}
                        onChange={() => setIsPublic(true)}
                    />
                    <Form.Check
                        type="radio"
                        label={<><i className="bi bi-lock"></i> <b>Private</b> - Only you have access to this repository</>}
                        name="visibility"
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