from typing import Literal
from fastapi import Request, Response
from httpx import AsyncClient, HTTPError
from app.api.config.exception_handler import RegistryException
from app.api.config.logutil import LOGGER

class RegistryClient:

    def __init__(self, client: AsyncClient, host: str, port: str, secured: bool = False):
        self.client = client
        self.host = host
        self.port = port
        self.secured = secured

    def _get_scheme(self) -> str:
        return "https://" if self.secured else "http://"

    def _create_manifest_path(self, repo_name: str, digest: str | None = None, tag_name: str | None = None) -> str:
        host = self.host
        port = self.port
        scheme = self._get_scheme()
        ref = tag_name if digest is None else digest
        return f"{scheme}{host}:{port}/v2/{repo_name}/manifests/{ref}"

    async def _request(self, method: Literal["GET", "DELETE"], url: str, token: str, **kwargs) -> Response:
        headers = kwargs.pop('headers', {})
        headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self.client.request(method, url, headers=headers) 
        except HTTPError as e:
            LOGGER.error(f"HTTP error when calling Distribution (method={method} url={url} status=502): \n{e}")
            raise RegistryException(502, str(e))    
            
        if response.status_code not in (200, 202, 404):
            body = response.text()
            LOGGER.error(f"Unexpected HTTP response when calling Distribution (method={method} url={url} status={response.status_code}): \n{body}")
            raise RegistryException(response.status_code, body)

        return response

    async def get_manifest(self, repo_name: str, tag_name: str, token: str) -> Response:
        url = self._create_manifest_path(repo_name, tag_name)
        headers = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json, "
                      "application/vnd.oci.image.index.v1+json, "
                      "application/vnd.oci.image.manifest.v1+json"
        }
        return await self._request("GET", url, token, headers=headers)
    
    async def delete_manifest(self, repo_name: str, digest: str, token: str) -> Response:
        url = self._create_manifest_path(repo_name, digest)
        return await self._request("DELETE", url, token)

def get_registry_client(request: Request = Request) -> RegistryClient:
    return request.app.registry_client
