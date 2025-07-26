import { useEffect, useState } from "react";
import { Button, Form, Spinner } from "react-bootstrap";
import { useParams, useNavigate } from "react-router-dom";
import { UserService, UserDTO } from "../api/user.api";
import { AxiosError, AxiosResponse } from "axios";
import { getJwtUsername } from "../util/localstorage";

export const ProfilePage = () => {
  const { username: profileUsername } = useParams<{ username: string }>();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserDTO>();
  const [updateUser, setUpdateUser] = useState<UserDTO | null>(null);
  const [isMyProfile, setIsMyProfile] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
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
          console.error("Not found - either a typo or access denied.");
        } else {
            console.error(err);
        }
      });
  };

  const handleEdit = () => {
    setUpdateUser(user ? { ...user } : null);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setUpdateUser(user ? { ...user } : null);
    setIsEditing(false);
  };

  const handleSave = () => {
    if (!updateUser) return;
    setSaving(true);

    const dto: UserDTO = {
      ...updateUser,
      first_name: updateUser.first_name ?? "",
      last_name: updateUser.last_name ?? "",
      bio: updateUser.bio ?? "",
      email: updateUser.email ?? "",
    };

    UserService.UpdateMyProfile(dto).then((res) => {
        setUser(res.data);
        setIsEditing(false);
      })
      .catch((err) => {
        console.error(err);
        alert("Failed to update profile");
      })
      .finally(() => setSaving(false));
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
      <h2 className="mb-4 text-center">{user.username}</h2>

      <Form>
        {/* First Name */}
        <Form.Group className="mb-3">
          <Form.Label>First Name</Form.Label>
          <Form.Control
            type="text"
            value={updateUser?.first_name ?? ""}
            readOnly={!isEditing}
            onChange={(e) =>
              setUpdateUser((prev) =>
                prev ? { ...prev, first_name: e.target.value } : prev
              )
            }
          />
        </Form.Group>

        {/* Last Name */}
        <Form.Group className="mb-3">
          <Form.Label>Last Name</Form.Label>
          <Form.Control
            type="text"
            value={updateUser?.last_name ?? ""}
            readOnly={!isEditing}
            onChange={(e) =>
              setUpdateUser((prev) =>
                prev ? { ...prev, last_name: e.target.value } : prev
              )
            }
          />
        </Form.Group>

        {/* Bio */}
        <Form.Group className="mb-3">
          <Form.Label>Bio</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            value={updateUser?.bio ?? ""}
            readOnly={!isEditing}
            onChange={(e) =>
              setUpdateUser((prev) =>
                prev ? { ...prev, bio: e.target.value } : prev
              )
            }
          />
        </Form.Group>

        {/* Email */}
        <Form.Group className="mb-3">
          <Form.Label>Email</Form.Label>
          <Form.Control
            type="email"
            value={updateUser?.email ?? ""}
            readOnly={!isEditing}
            onChange={(e) =>
              setUpdateUser((prev) =>
                prev ? { ...prev, email: e.target.value } : prev
              )
            }
          />
        </Form.Group>
      </Form>

      {isMyProfile && (
        <div className="d-flex justify-content-between mt-4">
          {!isEditing ? (
            <>
            <a href="/password-change-required" target="_blank" rel="noopener noreferrer"
            style={{ textDecoration: "underline", color: "#007bff", cursor: "pointer" }}>
            Change Password
            </a>
          <Button variant="light" style={{backgroundColor: "white",border: "1px solid #ddd",padding: "8px 16px"}} onClick={handleEdit}>
            <i className="bi bi-pencil"></i> Edit Profile
          </Button>
            </>
          ) : (
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
    </div>
  );
};
