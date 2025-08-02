import React, { useEffect, useRef, useState } from 'react';
import { OrganizationDTOBasic, OrganizationService, OrgDescUpdateDTO } from '../api/org.api';
import { ToastType, useToastStore } from '../util/toastStore';
import { Alert, FloatingLabel } from 'react-bootstrap';
import { AxiosError } from 'axios';
import { getJwtId } from '../util/localstorage';
import { fileToBase64 } from '../util/image';

export const OrgOverview: React.FC<{ isActive: boolean; org: OrganizationDTOBasic, setOrg: any }> = (props) => {
    const [isEditing, setIsEditing] = useState(false);
    const [newDesc, setNewDesc] = useState(props.org.desc);
    const [error, setError] = useState('');
    const [amOwnerOfOrg, setAmOwnerOfOrg] = useState(false);
    const [imagePreview, setImagePreview] = useState<string | null>(OrganizationService.GetImageURI(props.org.image));
    const fileInputRef = useRef<HTMLInputElement>(null);
    const addToast = useToastStore((state) => state.addToast);

    const checkIfIamOwnerOfOrg = () => {
        if (getJwtId() === props.org.owner_id) {
            setAmOwnerOfOrg(true);
        }
    };

    useEffect(() => {
        if (props.isActive) {
            checkIfIamOwnerOfOrg();
        }
    }, [props.isActive]);

    const updateDescription = () => {
        setIsEditing(false);
        const dto: OrgDescUpdateDTO = { desc: newDesc };

        OrganizationService.UpdateOrgDescByName(props.org.name, dto)
            .then((res) => {
                props.setOrg({ ...props.org, ...res.data });
                addToast(`Updated the description of ${props.org.name}.`, ToastType.success);
                setError('');
            })
            .catch((err: AxiosError) => {
                setError((err.response?.data as any)?.detail?.message || 'Failed to update description.');
            });
    };

    const handleImageClick = () => {
        if (amOwnerOfOrg && fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!['image/png', 'image/jpeg'].includes(file.type)) {
            setError('Only PNG and JPEG files are allowed.');
            return;
        }

        if (file.size > 2 * 1024 * 1024) { // 2MB limit
            setError('Image size must be less than 2MB.');
            return;
        }

        const base64 = await fileToBase64(file);
        console.log(base64);
        OrganizationService.UpdateOrgImageByName(props.org.name, { image: base64 })
            .then((res) => {
                console.log(res.data.image);
                props.setOrg({ ...props.org, ...res.data });
                setImagePreview(OrganizationService.GetImageURI(res.data.image));
                addToast(`Updated image for ${props.org.name}. Your changes will be visible shortly.`, ToastType.success);
                setError('');
            })
            .catch((err: AxiosError) => {
                setError((err.response?.data as any)?.detail?.message || 'Failed to update image.');
            });
    };

    const clearImage = () => {
        OrganizationService.ClearOrgImageByName(props.org.name)
            .then((res) => {
                props.setOrg({ ...props.org, ...res.data });
                //setImagePreview(null);
                addToast(`Cleared image for ${props.org.name}. Your changes will be visible shortly.`, ToastType.success);
                setError('');
            })
            .catch((err: AxiosError) => {
                setError((err.response?.data as any)?.detail?.message || 'Failed to clear image.');
            });

        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div style={{ width: '80%', margin: 'auto' }}>
            {error && <Alert variant="danger">{error}</Alert>}

            {/* Org Image */}
            <div className="mb-3 text-center">
                <img
                    src={imagePreview || '/default-org.png'}
                    alt="Organization"
                    style={{ maxWidth: '200px', maxHeight: '200px', cursor: amOwnerOfOrg ? 'pointer' : 'default' }}
                    onClick={handleImageClick}
                />
                {amOwnerOfOrg && imagePreview && (
                    <div className="mt-2">
                        <button className="btn btn-sm btn-outline-danger" onClick={clearImage}>
                            Clear Image
                        </button>
                    </div>
                )}
                <input
                    type="file"
                    accept="image/png, image/jpeg"
                    style={{ display: 'none' }}
                    ref={fileInputRef}
                    onChange={handleImageChange}
                />
            </div>

            <hr />

            <div className="tab-pane fade show active" id="overview">
                {isEditing ? (
                    <div>
                        <textarea
                            className="form-control"
                            rows={7}
                            value={newDesc}
                            onChange={(e) => setNewDesc(e.target.value)}
                            autoFocus
                        />
                        <div className='mt-3'>
                            <button className="btn btn-primary me-2" onClick={updateDescription}>
                                Update description
                            </button>
                            <button className="btn btn-secondary" onClick={() => { setIsEditing(false); setNewDesc(props.org.desc); }}>
                                Cancel
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="d-flex align-items-center">
                        {props.org.desc !== "" ? (
                            <div className='repo-page-desc'>{props.org.desc}</div>
                        ) : (
                            <i className='repo-page-desc'>No description provided</i>
                        )}
                        {amOwnerOfOrg && (
                            <button className="btn btn-link p-0 ms-2" onClick={() => setIsEditing(true)}>
                                <i className="bi bi-pencil"></i>
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};


// =======
//     <div className="d-flex flex-column align-items-center text-center mt-4" style={{ maxWidth: '80%', margin: '0 auto' }}>
//         {/* Org Image */}
//         <img src={OrganizationService.GetImageURI(props.org.image)} className="mb-3" />

//         {/* Main Content */}
//         <div className="tab-pane fade show active" id="overview" style={{ maxWidth: '700px', width: '100%' }}>
//             {error && <Alert variant="danger">{error}</Alert>}

//             {isEditing ? (
//                 <div>
//                     <textarea
//                         className="form-control text-center"
//                         rows={7}
//                         value={newDesc}
//                         onChange={(e) => setNewDesc(e.target.value)}
//                         autoFocus
//                     />
//                     <div className="mt-3 d-flex justify-content-center">
//                         <button className="btn btn-primary me-2" onClick={updateDescription}>
//                             Update description
//                         </button>
//                         <button className="btn btn-secondary" onClick={() => { setIsEditing(false); setNewDesc(props.org.desc); }}>
//                             Cancel
//                         </button>
//                     </div>
//                 </div>
//             ) : (
//                 <div className="d-flex align-items-start justify-content-center">
//                     <div className="repo-page-desc">{props.org.desc}</div>
//                     {amOwnerOfOrg && (
//                         <button className="btn btn-link p-0 ms-2" onClick={() => setIsEditing(true)}>
//                             <i className="bi bi-pencil"></i>
//                         </button>
//                     )}
//                 </div>
//             )}
//         </div>
//     </div>
// );

// };