import { useState } from 'react';
import { Form, Button, Alert } from 'react-bootstrap';
import { UserPasswordChangeDTO, UserService } from '../api/user.api';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { clearJWT } from '../util/localstorage';

export const UserPasswordChangeRequired = () => {
    let navigate = useNavigate();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmNewPassword, setConfirmNewPassword] = useState('');
    const [error, setError] = useState('');

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

        UserService.ChangePassword(dto).then(() => {
            clearJWT();
            navigate("/login", { replace: true });
        }).catch((err: AxiosError) => {
            console.error(err);
            setError((err.response?.data as any)["detail"]["message"]);
        });
    };

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
                <p className="text-muted text-center">
                    You will be signed out after this.
                </p>
            </div>
        </div>
    );
}