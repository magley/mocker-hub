import { useState, useEffect } from 'react';
import { Form, Button, Alert } from 'react-bootstrap';
import { jwtDecode } from 'jwt-decode'; 
import { UserPasswordChangeDTO, TokenDTO, Token, UserService } from '../api/user.api';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';

export const UserPasswordChangeRequired = () => {
    let navigate = useNavigate();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmNewPassword, setConfirmNewPassword] = useState('');
    const [error, setError] = useState('');
    const [roles, setRoles] = useState<string[]>([]);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            setError("No token found. Please log in again.");
            return;
        }
    
        try {
            const decoded: Token = jwtDecode(token);
            setRoles(decoded.role);
        } catch (err) {
            setError("Invalid token.");
        }
    }, []);
    

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword !== confirmNewPassword) {
            setError('New password and new password confirmation do not match');
            return;
        }

        let dto: UserPasswordChangeDTO = {
            old_password: oldPassword,
            new_password: newPassword
        };

        UserService.ChangePassword(dto).then((res) => {
            let token: TokenDTO = res.data;
            console.log(token);
            if (token.access_token) {
                localStorage.setItem("token", token.access_token)
            }
            navigate("/", { replace: true });
        }).catch((err: AxiosError) => {
            setError((err.response?.data as any)["detail"]["message"]);
        });

    };

    if (!roles.includes("user") && !roles.includes("admin") && !roles.includes("superadmin")) {
        return (
            <div className="container mt-5 d-flex justify-content-center">
                <Alert variant="danger">You do not have permission to change your password.</Alert>
            </div>
        )
    } 

    return (
        <div className="container mt-5 d-flex justify-content-center">
            <div className="w-100" style={{ maxWidth: '400px' }}>
                <h2 className="text-center">Password change required</h2>
                <p className="text-center">Please change your password before continuing.</p>
                <Form onSubmit={handleSubmit}>
                    <Form.Group controlId="oldPassword">
                        <Form.Label>Old Password</Form.Label>
                        <Form.Control
                            type="password"
                            value={oldPassword}
                            onChange={(e) => setOldPassword(e.target.value)}
                            required
                        />
                    </Form.Group>

                    <Form.Group controlId="newPassword">
                        <Form.Label>New Password</Form.Label>
                        <Form.Control
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            required
                        />
                    </Form.Group>

                    <Form.Group controlId="confirmNewPassword">
                        <Form.Label>Confirm New Password</Form.Label>
                        <Form.Control
                            type="password"
                            value={confirmNewPassword}
                            onChange={(e) => setConfirmNewPassword(e.target.value)}
                            required
                        />
                    </Form.Group>

                    {error && <Alert variant="danger" className='mt-3'>{error}</Alert>}

                    <Button variant="primary" type="submit" className="mt-3 w-100">
                        Change Password
                    </Button>
                </Form>
                {/* <p className="text-muted text-center">
                    You will be signed out after this.
                </p> */}
            </div>
        </div>
    );


}