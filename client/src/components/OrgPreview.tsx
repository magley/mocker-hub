import React from "react";
import { OrganizationDTOBasic } from "../api/org.api";
import { Card, Col, Row } from "react-bootstrap";
import { OrganizationService } from "../api/org.api";
import { Link } from "react-router-dom";
import { getJwtId } from "../util/localstorage";

export const OrgPreview: React.FC<{ org: OrganizationDTOBasic }> = ({
  org,
}) => {
  const isOwner = getJwtId() === org.owner_id;

  return (
    <Col key={org.id} xs={12}>
      <Card>
        <Card.Body>
          <Row className="align-items-center">

            {/* Left column - Image */}
            <Col md={2} className="mb-3">
              {org.image && (
                <img
                  src={OrganizationService.GetImageURI(org.image)}
                  alt={org.name}
                  style={{maxHeight: "100px", maxWidth: "100%", objectFit: "cover",
                  }}
                />
              )}
            </Col>

            {/* Right column */}
            <Col md={10}>
            
              {/* Organization Title with React Router Link */}
              <Card.Title>
                <Link to={`/o/${org.name}`} className="text-primary">
                  <span>{org.name}</span>
                </Link>
              </Card.Title>

              {/* Owner info */}
              <Card.Text className="text-muted" style={{ fontSize: "0.85rem" }}>
                <strong>
                  {isOwner
                    ? "You are an owner of this organisation"
                    : "You are a member of this organisation"}
                </strong>
              </Card.Text>

              {/* Description */}
              {org.desc && (
                <Card.Text style={{ fontSize: "0.9rem" }}>
                    {org.desc.length > 201 ? `${org.desc.slice(0, 201)}...` : org.desc}
                    </Card.Text>
              )}
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </Col>
  );
};
