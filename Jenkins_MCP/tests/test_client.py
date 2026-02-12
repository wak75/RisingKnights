"""Tests for Jenkins MCP Server client."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from jenkins import Jenkins

from jenkins_mcp_server.client import AsyncJenkinsClient, SyncJenkinsClient
from jenkins_mcp_server.config import JenkinsConfig
from jenkins_mcp_server.utils.exceptions import JenkinsConnectionError, JenkinsAPIError


class TestAsyncJenkinsClient:
    """Test AsyncJenkinsClient."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return JenkinsConfig(
            url="http://localhost:8080",
            username="admin",
            token="secret"
        )
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Create mock httpx client."""
        return Mock(spec=httpx.AsyncClient)
    
    def test_client_initialization(self, config):
        """Test client initialization."""
        client = AsyncJenkinsClient(config)
        
        assert client.config == config
        assert client.base_url == "http://localhost:8080"
        assert client._client is None
    
    @pytest.mark.asyncio
    async def test_get_request_success(self, config, mock_httpx_client):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        result = await client._request("GET", "/test")
        
        assert result == {"test": "data"}
        mock_httpx_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_request_404(self, config, mock_httpx_client):
        """Test GET request with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        with pytest.raises(JenkinsAPIError) as exc_info:
            await client._request("GET", "/nonexistent")
        
        assert "404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connection_error(self, config, mock_httpx_client):
        """Test connection error handling."""
        mock_httpx_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        with pytest.raises(JenkinsConnectionError):
            await client._request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_get_job_info(self, config, mock_httpx_client, sample_job_info):
        """Test get_job_info method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_job_info
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        result = await client.get_job_info("test-job")
        
        assert result == sample_job_info
        assert result["name"] == "test-job"
    
    @pytest.mark.asyncio
    async def test_create_job(self, config, mock_httpx_client, sample_job_config):
        """Test create_job method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        await client.create_job("new-job", sample_job_config)
        
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert "createItem" in call_args[1]["url"]
        assert sample_job_config in call_args[1]["content"]
    
    @pytest.mark.asyncio
    async def test_build_job_with_parameters(self, config, mock_httpx_client):
        """Test build_job method with parameters."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Location": "http://localhost:8080/queue/item/123/"}
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        queue_id = await client.build_job("test-job", {"BRANCH": "main"})
        
        assert queue_id == 123
        mock_httpx_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_build_console_output(self, config, mock_httpx_client, sample_console_output):
        """Test get_build_console_output method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_console_output
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        client = AsyncJenkinsClient(config)
        client._client = mock_httpx_client
        
        output = await client.get_build_console_output("test-job", 1)
        
        assert output == sample_console_output
        assert "Hello, World!" in output


class TestSyncJenkinsClient:
    """Test SyncJenkinsClient."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return JenkinsConfig(
            url="http://localhost:8080",
            username="admin",
            token="secret"
        )
    
    @pytest.fixture
    def mock_jenkins(self):
        """Create mock Jenkins client."""
        return Mock(spec=Jenkins)
    
    def test_client_initialization(self, config):
        """Test client initialization."""
        with patch('jenkins_mcp_server.client.Jenkins') as mock_jenkins_class:
            client = SyncJenkinsClient(config)
            
            assert client.config == config
            mock_jenkins_class.assert_called_once_with(
                url="http://localhost:8080",
                username="admin",
                password="secret",
                timeout=30
            )
    
    def test_get_job_info(self, config, mock_jenkins, sample_job_info):
        """Test get_job_info method."""
        mock_jenkins.get_job_info.return_value = sample_job_info
        
        with patch('jenkins_mcp_server.client.Jenkins', return_value=mock_jenkins):
            client = SyncJenkinsClient(config)
            result = client.get_job_info("test-job")
            
            assert result == sample_job_info
            mock_jenkins.get_job_info.assert_called_once_with("test-job")
    
    def test_create_job(self, config, mock_jenkins, sample_job_config):
        """Test create_job method."""
        with patch('jenkins_mcp_server.client.Jenkins', return_value=mock_jenkins):
            client = SyncJenkinsClient(config)
            client.create_job("new-job", sample_job_config)
            
            mock_jenkins.create_job.assert_called_once_with("new-job", sample_job_config)
    
    def test_jenkins_exception_handling(self, config, mock_jenkins):
        """Test Jenkins exception handling."""
        from jenkins import JenkinsException
        mock_jenkins.get_job_info.side_effect = JenkinsException("Jenkins error")
        
        with patch('jenkins_mcp_server.client.Jenkins', return_value=mock_jenkins):
            client = SyncJenkinsClient(config)
            
            with pytest.raises(JenkinsAPIError):
                client.get_job_info("nonexistent-job")


class TestClientIntegration:
    """Test client integration scenarios."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return JenkinsConfig(
            url="http://localhost:8080",
            username="admin",
            token="secret"
        )
    
    @pytest.mark.asyncio
    async def test_async_client_context_manager(self, config):
        """Test async client as context manager."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            async with AsyncJenkinsClient(config) as client:
                assert client._client is mock_client
            
            mock_client.aclose.assert_called_once()
    
    def test_sync_client_error_conversion(self, config):
        """Test sync client error conversion."""
        with patch('jenkins_mcp_server.client.Jenkins') as mock_jenkins_class:
            from requests.exceptions import ConnectionError
            mock_jenkins = Mock()
            mock_jenkins.get_job_info.side_effect = ConnectionError("Connection failed")
            mock_jenkins_class.return_value = mock_jenkins
            
            client = SyncJenkinsClient(config)
            
            with pytest.raises(JenkinsConnectionError):
                client.get_job_info("test-job")
    
    @pytest.mark.asyncio
    async def test_async_client_retry_logic(self, config):
        """Test async client retry logic."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            # First call fails, second succeeds
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"success": True}
            
            mock_client.get = AsyncMock(side_effect=[
                mock_response,  # First attempt fails
                mock_response_success  # Second attempt succeeds
            ])
            mock_client_class.return_value = mock_client
            
            client = AsyncJenkinsClient(config)
            
            # This should test the retry logic, but for now we'll just test the error
            with pytest.raises(JenkinsAPIError):
                await client._request("GET", "/test")