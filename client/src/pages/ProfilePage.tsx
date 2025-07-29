import { useEffect, useState } from "react";
import { Alert, Button, Form, Spinner } from "react-bootstrap";
import { useParams, useNavigate, Link } from "react-router-dom";
import { UserService, UserDTO, UserBadge } from "../api/user.api";
import { AxiosError, AxiosResponse } from "axios";
import { getJwtUsername } from "../util/localstorage";
import { get_validation_error_readable } from "../util/http";
import { ToastType, useToastStore } from "../util/toastStore";
import { is } from "date-fns/locale";
import { BadgeUtils } from "../util/badge";

export const ProfilePage = () => {
  const { username: profileUsername } = useParams<{ username: string }>();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserDTO>();
  const [updateUser, setUpdateUser] = useState<UserDTO | null>(null);
  const [isMyProfile, setIsMyProfile] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const addToast = useToastStore((state) => state.addToast);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserProfile(profileUsername!);
  }, [profileUsername]);

  const fetchUserProfile = (uname: string) => {
    setLoading(true);

    UserService.GetUserProfile(uname).then((res: AxiosResponse<UserDTO>) => {
        setLoading(false);
        setUser(res.data);
        setUpdateUser(res.data);

        const myUsername = getJwtUsername();
        setIsMyProfile(myUsername === res.data.username);
      })
      .catch((err: AxiosError) => {
        if (err.response?.status === 404) {
          navigate("/");
          setError(get_validation_error_readable(err));
        } else {
            setError(get_validation_error_readable(err));
        }
      });
  };

  const handleEdit = () => {
    setUpdateUser(user ? { ...user } : null);
    setIsEditing(true);
    setError("");
  };

  const handleCancel = () => {
    setUpdateUser(user ? { ...user } : null);
    setIsEditing(false);
    setError("");
  };

  const handleSave = () => {
    if (!updateUser) return;
    setSaving(true);

    const dto: UserDTO = {
      ...updateUser,
      first_name: (updateUser.first_name ?? ""),
      last_name: updateUser.last_name ?? "",
      bio: updateUser.bio ?? "",
      email: updateUser.email ?? "",
    };

    UserService.UpdateMyProfile(dto).then((res) => {
        setUser(res.data);
        setIsEditing(false);
        setError("");
        addToast(`Successfully updated your profile`, ToastType.success);
      })
      .catch((err) => {
        console.error(err);
        setError(get_validation_error_readable(err));
      })
      .finally(() => setSaving(false));
  };

const sanitizeNameInput = (value: string): string => {
  let cleaned = value.replace(/[^a-zA-Z0-9.\-_ ]/g, "");
  cleaned = cleaned.replace(/\s+/g, " ");
  return cleaned;
};


  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  if (!user) {
    return <p className="text-center mt-5">User not found</p>;
  }

  return (
    <div className="container mt-4" style={{ maxWidth: "600px" }}>
      
      <div className="position-relative mb-4" style={{marginTop: "2rem"}}>
        <h1 className="text-center">{user.username}</h1>
        {isMyProfile && !isEditing && (
            <i className="bi bi-pencil" style={{position: "absolute", right: 0, cursor: "pointer", fontSize: "1.35rem", color: "#007bff", top: "0.5em"}} onClick={handleEdit}></i>
          )}
        {user.badge !== UserBadge.none && ( 
          <div className={`badge rounded-pill ${BadgeUtils.toBootstrapColor(user.badge)}`}
              style={{ fontSize: '0.7em', maxHeight: "20px", display: 'block', width: 'fit-content', margin: "0 auto" }}
          >
              <i className={`bi ${BadgeUtils.toBootstrapIcon(user.badge)}`}> </i>
              {BadgeUtils.toHumanText(user.badge)}
          </div>
        )}
      </div>

      <Form style={{ marginBottom: "2rem" }}>
        {/* First Name */}
        <Form.Group className="mb-3">
          <Form.Label style={{ fontWeight: isEditing ? 500 : 400 }}>First Name</Form.Label>
          <Form.Control
            type="text"
            value={updateUser?.first_name ?? ""}
            style={{borderColor: isEditing ? "#007bff" : "#ced4da"}}
            readOnly={!isEditing}
            maxLength={50} 
            onChange={(e) => {
              const sanitized = sanitizeNameInput(e.target.value);
              setUpdateUser((prev) =>
                prev ? { ...prev, first_name: sanitized } : prev
              );
            }}
          />
        </Form.Group>

        {/* Last Name */}
        <Form.Group className="mb-3">
          <Form.Label style={{ fontWeight: isEditing ? 500 : 400 }}>Last Name</Form.Label>
          <Form.Control
            type="text"
            value={updateUser?.last_name ?? ""}
            style={{borderColor: isEditing ? "#007bff" : "#ced4da"}}
            readOnly={!isEditing}
            maxLength={50}
            onChange={(e) => {
              const sanitized = sanitizeNameInput(e.target.value);
              setUpdateUser((prev) =>
                prev ? { ...prev, last_name: sanitized } : prev
              );
            }}
          />
        </Form.Group>

        {/* Bio */}
        <Form.Group className="mb-3">
          <Form.Label style={{ fontWeight: isEditing ? 500 : 400 }}>Bio</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            value={updateUser?.bio ?? ""}
            style={{borderColor: isEditing ? "#007bff" : "#ced4da"}}
            readOnly={!isEditing}
            maxLength={400} 
            onChange={(e) =>
              setUpdateUser((prev) =>
                prev ? { ...prev, bio: e.target.value } : prev
              )
            }
          />
        </Form.Group>

        {/* Email */}
        <Form.Group className="mb-3">
          <Form.Label style={{ fontWeight: isEditing ? 500 : 400 }}>Email</Form.Label>
          <Form.Control
            type="email"
            value={updateUser?.email ?? ""}
            style={{borderColor: isEditing ? "#007bff" : "#ced4da"}}
            readOnly={!isEditing}
            maxLength={50} 
            onChange={(e) =>
              setUpdateUser((prev) =>
                prev ? { ...prev, email: e.target.value } : prev
              )
            }
          />
        </Form.Group>
        {error && <Alert variant="danger" className='mt-3'>{error}</Alert>}
      </Form>

      {isMyProfile && (
        <div className="d-flex justify-content-between mt-4">
          {isEditing && (
            <>
              <Button variant="secondary" onClick={handleCancel}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save Changes"}
              </Button>
              </>
          )}
        </div>
      )}
      {!isEditing && (
        <div className="d-flex justify-content-between">
          {isMyProfile && (
          <a href="/password-change" rel="noopener noreferrer" style={{ textDecoration: "underline", color: "#007bff", cursor: "pointer" }}>
            Change Password
            </a>
        )}
          <Link to={`/u/${user.username}/repos`} className="text-decoration-none" style={{ color: "#007bff", fontWeight: 500 }}>
            <i className="bi bi-boxes me-2"></i>
            {isMyProfile ? "View My Repositories" : `View ${user.username}'s Repositories`}
          </Link>
        </div>
      )}
    </div>
  );
};
