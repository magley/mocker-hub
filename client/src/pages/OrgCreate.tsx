import React, { useRef, useState } from 'react';
import { Form, Button, Alert, Row, Col, Spinner } from 'react-bootstrap';
import './OrgCreate.css';
import { fileToBase64 } from '../util/image';
import { OrganizationCreateDTO, OrganizationService } from '../api/org.api';
import { AxiosError } from 'axios';
import { ToastType, useToastStore } from '../util/toastStore';
import { useNavigate } from 'react-router-dom';

export const OrganizationCreate = () => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [image, setImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [errors, setErrors] = useState<{ name?: string; description?: string; image?: string }>({});
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);

    const navigate = useNavigate();
    const addToast = useToastStore((state) => state.addToast);

    const validateForm = () => {
        const newErrors: { name?: string; description?: string; image?: string } = {};
        if (!name) newErrors.name = 'Name is required';
        if (!description) newErrors.description = 'Description is required';
        if (image) {
            if (!['image/png', 'image/jpeg'].includes(image.type)) newErrors.image = 'Only PNG and JPEG files are allowed';
        }

        return newErrors;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const formErrors = validateForm();
        if (Object.keys(formErrors).length === 0) {
            let base64: string | null = null;
            if (image) {
                base64 = await fileToBase64(image);
            }

            const dto: OrganizationCreateDTO = {
                name: name,
                desc: description,
                image: base64,
            };

            setError('');
            setErrors({});
            setLoading(true);
            OrganizationService.CreateOrganization(dto).then((res) => {
                const org = res.data;
                addToast(`Created organization ${org.name}`, ToastType.success);
                navigate(`/o/${org.name}`);
            }).catch((err: AxiosError) => {
                setError((err.response?.data as any)["detail"]["message"]);
            }).finally(() => {
                setLoading(false);
            });
        } else {
            setErrors(formErrors);
        }
    };

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files ? e.target.files[0] : null;
        setImage(file);
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            setImagePreview(imageUrl);
        } else {
            setImagePreview(null);
        }
    };

    const clearImage = () => {
        setImage(null);
        setImagePreview(null);

        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <Form onSubmit={handleSubmit} className='org-create'>
            <h1>Create a new organization</h1>

            <Form.Group controlId="formName">
                <Form.Label>Name</Form.Label>
                <Form.Control
                    type="text"
                    placeholder="Enter organization name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    isInvalid={!!errors.name}
                />
                <Form.Control.Feedback type="invalid">{errors.name}</Form.Control.Feedback>
            </Form.Group>

            <Form.Group controlId="formDescription">
                <Form.Label>Description</Form.Label>
                <Form.Control
                    type="text"
                    placeholder="Enter organization description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    isInvalid={!!errors.description}
                />
                <Form.Control.Feedback type="invalid">{errors.description}</Form.Control.Feedback>
            </Form.Group>

            <Form.Group controlId="formImage">
                <Form.Label>Image</Form.Label>
                <Row>
                    <Col>
                        <Form.Control
                            type="file"
                            accept="image/png, image/jpeg"
                            onChange={handleImageChange}
                            isInvalid={!!errors.image}
                            ref={fileInputRef}
                        />
                        <Form.Control.Feedback type="invalid">{errors.image}</Form.Control.Feedback>
                    </Col>
                    {imagePreview && (
                        <Col xs="auto">
                            <Button variant="danger" onClick={clearImage}>
                                Clear Image
                            </Button>
                        </Col>
                    )}
                </Row>
            </Form.Group>

            {imagePreview && (
                <div className="mb-3">
                    <img src={imagePreview} alt="Preview" style={{ maxWidth: '100%', height: 'auto' }} />
                </div>
            )}

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="d-flex justify-content-end mt-5">
                <Button variant="primary" type="submit">
                    {loading && (
                        <Spinner
                            as="span"
                            size="sm"
                            role="status"
                            aria-hidden="true"
                        > </Spinner>
                    )}
                    Create Organization
                </Button>
            </div>

        </Form>
    );

};