import base64
import datetime
import uuid

import jwt

from app.api.registry.registry_dto import RegistryAction, RegistryActionOperation

SECRET_KEY = ""
with open("/mnt/local/certs/private_key.pem", "r") as f:
    SECRET_KEY = f.read()
    
CERT_DER_B64 = ""
with open("/mnt/local/certs/cert.der.b64", "r") as f:
    CERT_DER_B64 = f.read()


def decode_auth_header(auth_token):
    """
    Decode the username and password fields from an HTTP Basic authorization
    header.

    ---
    
    `auth_token` is the encoded token. In other words, if the authorization
    header is:

        Authorization: Basic dhkj3h289,

    then `auth_token` must be `dhkj3h289`.

    ---

    Returns a pair of strings `username`, `password`.
    """
    decoded_bytes = base64.b64decode(auth_token).decode('utf-8')
    username, password = decoded_bytes.split(':')
    return username, password


def parse_scope(username: str, scope: str) -> RegistryAction:
    """
    Parse scope from Docker Registry request.

    `username` is the username of the user making the request.

    `scope` is the scope of resource access built into the JWT, or `None` if the
    Docker Registry request is just a login operation. For example:
    `repository:nginx:push,pull` means that the user wants access to push and
    pull to the official `nginx` repository.
    """

    scope_parts = scope.split(':')   
    if scope_parts[0] != 'repository':
        raise Exception(f"Unexpected scope type '{scope_parts[0]}'. Expecting 'repository'")
    repository = scope_parts[1]
    operations = [RegistryActionOperation(o) for o in scope_parts[2].split(',')]

    return RegistryAction(username=username, repo_canonical_name=repository, operations=operations)


def build_jwt_for_docker_registry(username: str, service: str, scope: str) -> str:
    """
    Create a JWT as required by Docker Registry.

    ---

    `username` is the name of the user.

    `service` is the name of the service requesting the JWT. In other words,
    this is the audience for the JWT. This value should be extracted from the
    HTTP request issued by Docker Registry.

    `scope` is the scope of resource access built into the JWT, or `None` if the
    Docker Registry request is just a login operation. For example:
    `repository:nginx:push,pull` means that the user wants access to push and
    pull to the official `nginx` repository.

    ---

    Returns a string representaiton of the encoded JWT.
    """
    now = datetime.datetime.now()

    token_payload = {
        'iss': 'localhost:8000', # TODO: ...?
        'sub': username,
        'aud': service,
        'exp': now + datetime.timedelta(hours=1),
        'nbf': now,
        'iat': now,
        'jti': str(uuid.uuid4()),
        'access': []
    }
    token_headers = { 
        'x5c': [CERT_DER_B64] 
    }

    if scope is not None:
        scope_parts = scope.split(':')   
        token_payload['access'] = [
            {
                'type': 'repository',
                'name': scope_parts[1],
                'actions': scope_parts[2].split(',')
            }
        ]

    return jwt.encode(token_payload, SECRET_KEY, algorithm='RS256', headers=token_headers)    
