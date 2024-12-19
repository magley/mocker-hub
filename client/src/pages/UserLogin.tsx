import { useState } from 'react';
import { Form, Button, Container, Row, Col, Alert } from 'react-bootstrap';
import './UserLogin.css';
import { TokenDTO, UserLoginDTO, UserService } from '../api/user.api';
import { AxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';
import { getJwtId, getJwtMustChangePassword, getJwtRole, getJwtUsername, setJWT } from '../util/localstorage';
import { useAuthStore } from '../util/store';

export const UserLogin = () => {
    let navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [error, setError] = useState('');
    const setRole = useAuthStore((state) => state.setRole);

    const handleChange = (e: any) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handleSubmit = (e: any) => {
        e.preventDefault();
        if (!formData.username || !formData.password) {
            setError('All fields are required');
            return;
        }

        setError('');

        let dto: UserLoginDTO = {
            username: formData.username,
            password: formData.password,
        };

        UserService.LoginUser(dto).then((res) => {
            let token: TokenDTO = res.data;
            setJWT(token.token);
            setRole(getJwtRole(), () => {
                if (getJwtMustChangePassword()) {
                    navigate("/password-change-required");
                } else {
                    const username = getJwtUsername();
                    navigate(`/u/${username}/repos`);
                }
            });
        }).catch((err: AxiosError) => {
            console.error(err);
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

    return (
        <Container className="login-container">
            <Row className="justify-content-md-center">
                <Col md={6}>
                    <h2 className="mt-5">Login</h2>
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

                        <div className="d-flex justify-content-center">
                            <Button variant="primary" type="submit" className="mt-3">
                                Login
                            </Button>
                        </div>
                    </Form>
                </Col>
            </Row>
        </Container>
    );
};
