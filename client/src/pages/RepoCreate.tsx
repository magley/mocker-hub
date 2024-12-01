import { useEffect, useState } from 'react';
import { Form, Button, DropdownButton, Dropdown, Col, Row, Alert } from 'react-bootstrap';
import './RepoCreate.css';

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
        // Load possible owners and organizations.

        setOwners([
            { name: "user 1", user_id: 1, organization_id: null },
            { name: "org 1", user_id: null, organization_id: 1 },
            { name: "org 2", user_id: null, organization_id: 2 },
        ]);

        // Set initial owner as the user who's currently logged in.

        setOwner(owners[0]);
    }, []);

    const userOrOrgToStr = (owner: Owner) => {
        if (owner.user_id != null) {
            return `User ${owner.user_id} (You)`;
        }
        if (owner.organization_id != null) {
            return `Organization ${owner.organization_id}`;
        }
        console.error(`Bad owner object: ${owner}`);
    }

    const handleSubmit = (event: React.FormEvent) => {
        event.preventDefault();
        const data = {
            name,
            owner,
            description,
            isPublic,
        };

        if (!data.name.trim()) {
            setError("You must enter the name of the repository.");
            return;
        }

        setError('');

        //console.log('Repository:', repository);
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
                                <Dropdown.Item key={o.user_id} eventKey={o.name}>
                                    {o.user_id} / {o.organization_id}
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
            {/* 
            <Form.Group controlId="formName">
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
                        <Dropdown.Item key={o.user_id} eventKey={o.name}>
                            {o.user_id} / {o.organization_id}
                        </Dropdown.Item>
                    ))}
                </DropdownButton>

                <Form.Label>Name</Form.Label>
                <Form.Control
                    type="text"
                    placeholder="Enter repository name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />

            </Form.Group> */}

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