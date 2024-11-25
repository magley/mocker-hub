import { useState } from 'react';
import { Form, Button, Container, Row, Col, Alert } from 'react-bootstrap';
import './UserRegistration.css';
import { UserDTO, UserRegisterDTO, UserService } from '../api/user.api';
import { AxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';

export const UserRegistration = () => {
    let navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');

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
            return;
        }
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        setError('');

        let dto: UserRegisterDTO = {
            email: formData.email,
            username: formData.username,
            password: formData.password,
        };
        UserService.RegisterRegularUser(dto).then((res) => {
            let user: UserDTO = res.data;
            console.log(user);
            navigate("/login");
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

    return (
        <Container className="registration-container">
            <Row className="justify-content-md-center">
                <Col md={6}>
                    <h2 className="mt-5">Register</h2>
                    {error && <Alert variant="danger">{error}</Alert>}
                    <Form onSubmit={handleSubmit}>
                        <Form.Group as={Row} controlId="formUsername">
                            <Form.Label column sm={3}>Username</Form.Label>
                            <Col sm={9}>
                                <Form.Control
                                    type="text"
                                    name="username"
                                    placeholder="Enter your username"
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
                                    placeholder="Enter your password"
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
                                    placeholder="Confirm your password"
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
