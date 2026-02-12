"""Jenkins API client with enhanced error handling and async support."""

import asyncio
import base64
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, quote
import xml.etree.ElementTree as ET

import httpx
import jenkins
from jenkins import Jenkins

from .config import JenkinsConfig
from .utils import (
    JenkinsConnectionError,
    JenkinsAuthenticationError,
    JenkinsNotFoundError,
    JenkinsPermissionError,
    JenkinsBuildError,
    get_logger,
)


class AsyncJenkinsClient:
    """Async Jenkins API client wrapper."""
    
    def __init__(self, config: JenkinsConfig):
        """Initialize the async Jenkins client."""
        self.config = config
        self.base_url = config.url
        self.logger = get_logger("client")
        
        # Setup authentication
        self.auth = None
        if config.username and config.token:
            self.auth = httpx.BasicAuth(config.username, config.token)
        elif config.username and config.password:
            self.auth = httpx.BasicAuth(config.username, config.password)
        
        # HTTP client configuration
        self.client_config = {
            "timeout": httpx.Timeout(config.timeout),
            "verify": config.verify_ssl,
            "auth": self.auth,
            "headers": {
                "User-Agent": "Jenkins-MCP-Server/1.0.0",
                "Accept": "application/json",
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(**self.client_config)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def _make_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None,
        data: Optional[Union[str, Dict]] = None,
        headers: Optional[Dict] = None
    ) -> httpx.Response:
        """Make HTTP request with error handling and retries."""
        url = urljoin(self.base_url, path)
        request_headers = self.client_config["headers"].copy()
        if headers:
            request_headers.update(headers)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params, headers=request_headers)
                elif method.upper() == "POST":
                    if isinstance(data, dict):
                        response = await self.client.post(url, json=data, params=params, headers=request_headers)
                    else:
                        response = await self.client.post(url, content=data, params=params, headers=request_headers)
                elif method.upper() == "PUT":
                    if isinstance(data, dict):
                        response = await self.client.put(url, json=data, params=params, headers=request_headers)
                    else:
                        response = await self.client.put(url, content=data, params=params, headers=request_headers)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url, params=params, headers=request_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle HTTP errors
                if response.status_code == 401:
                    raise JenkinsAuthenticationError("Authentication failed")
                elif response.status_code == 403:
                    raise JenkinsPermissionError("Permission denied")
                elif response.status_code == 404:
                    raise JenkinsNotFoundError("Resource not found")
                elif response.status_code >= 500:
                    if attempt < self.config.max_retries:
                        self.logger.warning(f"Server error {response.status_code}, retrying...")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise JenkinsConnectionError(f"Server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise JenkinsBuildError(f"Request failed: {response.status_code} - {response.text}")
                
                return response
                
            except httpx.RequestError as e:
                if attempt < self.config.max_retries:
                    self.logger.warning(f"Request error: {e}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise JenkinsConnectionError(f"Connection failed: {e}")
        
        raise JenkinsConnectionError("Max retries exceeded")
    
    async def get_json(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Get JSON response from Jenkins API."""
        if not path.endswith("/api/json"):
            if path.endswith("/"):
                path += "api/json"
            else:
                path += "/api/json"
        
        response = await self._make_request("GET", path, params=params)
        try:
            return response.json()
        except json.JSONDecodeError:
            raise JenkinsBuildError("Invalid JSON response from Jenkins")
    
    async def get_text(self, path: str, params: Optional[Dict] = None) -> str:
        """Get text response from Jenkins API."""
        response = await self._make_request("GET", path, params=params)
        return response.text
    
    async def post_json(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post JSON data to Jenkins API."""
        headers = {"Content-Type": "application/json"}
        response = await self._make_request("POST", path, data=data, headers=headers)
        if response.text:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"message": response.text}
        return {"status": "success"}
    
    async def post_form(self, path: str, data: Dict[str, Any]) -> str:
        """Post form data to Jenkins API."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        form_data = "&".join([f"{k}={quote(str(v))}" for k, v in data.items()])
        response = await self._make_request("POST", path, data=form_data, headers=headers)
        return response.text
    
    async def post_xml(self, path: str, xml_data: str) -> str:
        """Post XML data to Jenkins API."""
        headers = {"Content-Type": "application/xml"}
        response = await self._make_request("POST", path, data=xml_data, headers=headers)
        return response.text


class SyncJenkinsClient:
    """Synchronous Jenkins client using python-jenkins library."""
    
    def __init__(self, config: JenkinsConfig):
        """Initialize the sync Jenkins client."""
        self.config = config
        self.logger = get_logger("sync_client")
        
        try:
            self.jenkins = Jenkins(
                url=config.url,
                username=config.username,
                password=config.token or config.password,
                timeout=config.timeout,
            )
            
            # Configure SSL verification
            if hasattr(self.jenkins, '_session'):
                self.jenkins._session.verify = config.verify_ssl
                
            # Disable SSL warnings if verification is disabled
            if not config.verify_ssl:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Test connection
            self.jenkins.get_whoami()
            self.logger.info("Successfully connected to Jenkins")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Jenkins: {e}")
            raise JenkinsConnectionError(f"Failed to connect to Jenkins: {e}")
    
    def get_version(self) -> str:
        """Get Jenkins version."""
        try:
            return self.jenkins.get_version()
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get Jenkins version: {e}")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all Jenkins jobs."""
        try:
            return self.jenkins.get_jobs()
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get jobs: {e}")
    
    def get_job_info(self, name: str) -> Dict[str, Any]:
        """Get job information."""
        try:
            return self.jenkins.get_job_info(name)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Job '{name}' not found")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get job info: {e}")
    
    def get_job_config(self, name: str) -> str:
        """Get job XML configuration."""
        try:
            return self.jenkins.get_job_config(name)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Job '{name}' not found")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get job config: {e}")
    
    def create_job(self, name: str, config_xml: str) -> None:
        """Create a new job."""
        try:
            self.jenkins.create_job(name, config_xml)
        except jenkins.JenkinsException as e:
            if "already exists" in str(e).lower():
                raise JenkinsBuildError(f"Job '{name}' already exists")
            raise JenkinsBuildError(f"Failed to create job: {e}")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to create job: {e}")
    
    def build_job(self, name: str, parameters: Optional[Dict] = None) -> int:
        """Build a job and return the build number."""
        try:
            if parameters:
                return self.jenkins.build_job(name, parameters)
            else:
                return self.jenkins.build_job(name)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Job '{name}' not found")
        except Exception as e:
            raise JenkinsBuildError(f"Failed to build job: {e}")
    
    def get_build_info(self, name: str, number: int) -> Dict[str, Any]:
        """Get build information."""
        try:
            return self.jenkins.get_build_info(name, number)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Build #{number} for job '{name}' not found")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get build info: {e}")
    
    def get_build_console_output(self, name: str, number: int) -> str:
        """Get build console output."""
        try:
            return self.jenkins.get_build_console_output(name, number)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Build #{number} for job '{name}' not found")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get build console output: {e}")
    
    def delete_job(self, name: str) -> None:
        """Delete a job."""
        try:
            self.jenkins.delete_job(name)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Job '{name}' not found")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to delete job: {e}")
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all Jenkins nodes."""
        try:
            return self.jenkins.get_nodes()
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get nodes: {e}")
    
    def get_node_info(self, name: str) -> Dict[str, Any]:
        """Get node information."""
        try:
            return self.jenkins.get_node_info(name)
        except jenkins.NotFoundException:
            raise JenkinsNotFoundError(f"Node '{name}' not found")
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get node info: {e}")
    
    def get_plugins(self) -> Dict[str, Any]:
        """Get installed plugins."""
        try:
            return self.jenkins.get_plugins()
        except Exception as e:
            raise JenkinsConnectionError(f"Failed to get plugins: {e}")
    
    def install_plugin(self, name: str) -> bool:
        """Install a plugin."""
        try:
            return self.jenkins.install_plugin(name)
        except Exception as e:
            raise JenkinsBuildError(f"Failed to install plugin: {e}")


def create_jenkins_client(config: JenkinsConfig) -> SyncJenkinsClient:
    """Create a Jenkins client instance."""
    return SyncJenkinsClient(config)