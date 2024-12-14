import { useState } from 'react';
import { Form, Button, Container, Row, Col, Alert } from 'react-bootstrap';
import './UserRegistration.css';
import { UserRegisterDTO, UserService } from '../api/user.api';
import { AxiosError } from 'axios';

const initialFormState = {
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
}

export const UserAdminRegistration = () => {
    const [formData, setFormData] = useState(initialFormState);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleChange = (e: any) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handleSubmit = (e: any) => {
        e.preventDefault();
        if (!formData.username || !formData.email || !formData.password || !formData.confirmPassword) {
            setError('All fields are required');
            setSuccess('');
            return;
        }
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setSuccess('');
            return;
        }
        setError('');
        setSuccess('');

        let dto: UserRegisterDTO = {
            email: formData.email,
            username: formData.username,
            password: formData.password,
        };
        UserService.RegisterAdmin(dto).then(() => {
            setFormData(initialFormState);
            setSuccess("Admin " + dto.username + " is successfully registered!")
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

    return (
        <Container className="registration-container">
            <Row className="justify-content-md-center">
                <Col md={6}>
                    <h2 className="mt-5">Register admin</h2>
                    {error && <Alert variant="danger">{error}</Alert>}
                    {success && <Alert variant="success">{success}</Alert>}
                    <Form onSubmit={handleSubmit}>
                        <Form.Group as={Row} controlId="formUsername">
                            <Form.Label column sm={3}>Username</Form.Label>
                            <Col sm={9}>
                                <Form.Control
                                    type="text"
                                    name="username"
                                    placeholder="Enter admin username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    required
                                />
                            </Col>
                        </Form.Group>

                        <Form.Group as={Row} controlId="formEmail">
                            <Form.Label column sm={3}>Email</Form.Label>
                            <Col sm={9}>
                                <Form.Control
                                    type="email"
                                    name="email"
                                    placeholder="user@example.org"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                />
                            </Col>
                        </Form.Group>

                        <Form.Group as={Row} controlId="formPassword">
                            <Form.Label column sm={3}>Password</Form.Label>
                            <Col sm={9}>
                                <Form.Control
                                    type="password"
                                    name="password"
                                    placeholder="Enter admin password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                />
                            </Col>
                        </Form.Group>

                        <Form.Group as={Row} controlId="formConfirmPassword">
                            <Form.Label column sm={3}>Confirm Password</Form.Label>
                            <Col sm={9}>
                                <Form.Control
                                    type="password"
                                    name="confirmPassword"
                                    placeholder="Confirm admin password"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
                                />
                            </Col>
                        </Form.Group>

                        <div className="d-flex justify-content-center">
                            <Button variant="primary" type="submit" className="mt-3">
                                Register
                            </Button>
                        </div>
                    </Form>
                </Col>
            </Row>
        </Container>
    );
};
