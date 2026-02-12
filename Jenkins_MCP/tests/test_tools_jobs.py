"""Tests for Jenkins tools."""

import pytest
from unittest.mock import Mock, AsyncMock

from jenkins_mcp_server.tools.jobs import (
    create_job, get_job, update_job, delete_job, 
    list_jobs, enable_job, disable_job
)


class TestJobTools:
    """Test job management tools."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Jenkins client."""
        client = Mock()
        client.create_job = AsyncMock()
        client.get_job_info = AsyncMock()
        client.update_job = AsyncMock()
        client.delete_job = AsyncMock()
        client.get_all_jobs = AsyncMock()
        client.enable_job = AsyncMock()
        client.disable_job = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_create_job_freestyle(self, mock_client, sample_job_config):
        """Test creating a freestyle job."""
        mock_client.create_job.return_value = True
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await create_job(
                name="test-job",
                job_type="freestyle",
                description="Test job"
            )
            
            assert result["success"] is True
            assert result["job_name"] == "test-job"
            mock_client.create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_job_pipeline(self, mock_client):
        """Test creating a pipeline job."""
        mock_client.create_job.return_value = True
        
        pipeline_script = """
        pipeline {
            agent any
            stages {
                stage('Test') {
                    steps {
                        echo 'Hello World'
                    }
                }
            }
        }
        """
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await create_job(
                name="pipeline-job",
                job_type="pipeline",
                pipeline_script=pipeline_script
            )
            
            assert result["success"] is True
            assert result["job_name"] == "pipeline-job"
            mock_client.create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_job_info(self, mock_client, sample_job_info):
        """Test getting job information."""
        mock_client.get_job_info.return_value = sample_job_info
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await get_job("test-job")
            
            assert result["name"] == "test-job"
            assert result["buildable"] is True
            mock_client.get_job_info.assert_called_once_with("test-job")
    
    @pytest.mark.asyncio
    async def test_delete_job(self, mock_client):
        """Test deleting a job."""
        mock_client.delete_job.return_value = True
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await delete_job("test-job")
            
            assert result["success"] is True
            assert result["message"] == "Job 'test-job' deleted successfully"
            mock_client.delete_job.assert_called_once_with("test-job")
    
    @pytest.mark.asyncio
    async def test_list_jobs(self, mock_client):
        """Test listing jobs."""
        job_list = [
            {"name": "job1", "color": "blue"},
            {"name": "job2", "color": "red"},
            {"name": "job3", "color": "disabled"}
        ]
        mock_client.get_all_jobs.return_value = job_list
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await list_jobs()
            
            assert len(result["jobs"]) == 3
            assert result["total_count"] == 3
            mock_client.get_all_jobs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_jobs_with_filter(self, mock_client):
        """Test listing jobs with status filter."""
        job_list = [
            {"name": "job1", "color": "blue"},
            {"name": "job2", "color": "red"},
            {"name": "job3", "color": "disabled"}
        ]
        mock_client.get_all_jobs.return_value = job_list
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await list_jobs(status_filter="success")
            
            # Should only return blue (successful) jobs
            success_jobs = [job for job in result["jobs"] if job["color"] == "blue"]
            assert len(success_jobs) == 1
    
    @pytest.mark.asyncio
    async def test_enable_job(self, mock_client):
        """Test enabling a job."""
        mock_client.enable_job.return_value = True
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await enable_job("test-job")
            
            assert result["success"] is True
            assert result["message"] == "Job 'test-job' enabled successfully"
            mock_client.enable_job.assert_called_once_with("test-job")
    
    @pytest.mark.asyncio
    async def test_disable_job(self, mock_client):
        """Test disabling a job."""
        mock_client.disable_job.return_value = True
        
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client):
            result = await disable_job("test-job")
            
            assert result["success"] is True
            assert result["message"] == "Job 'test-job' disabled successfully"
            mock_client.disable_job.assert_called_once_with("test-job")


class TestJobToolsErrorHandling:
    """Test error handling in job tools."""
    
    @pytest.fixture
    def mock_client_with_errors(self):
        """Create mock Jenkins client that raises errors."""
        from jenkins_mcp_server.utils.exceptions import JenkinsAPIError
        
        client = Mock()
        client.get_job_info = AsyncMock(side_effect=JenkinsAPIError("Job not found"))
        client.create_job = AsyncMock(side_effect=JenkinsAPIError("Job already exists"))
        return client
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, mock_client_with_errors):
        """Test getting non-existent job."""
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client_with_errors):
            result = await get_job("nonexistent-job")
            
            assert result["error"] is not None
            assert "Job not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_job_already_exists(self, mock_client_with_errors):
        """Test creating job that already exists."""
        with pytest.mock.patch('jenkins_mcp_server.tools.jobs.get_jenkins_client', return_value=mock_client_with_errors):
            result = await create_job("existing-job", "freestyle")
            
            assert result["success"] is False
            assert "Job already exists" in result["error"]


class TestJobToolsValidation:
    """Test input validation for job tools."""
    
    @pytest.mark.asyncio
    async def test_create_job_invalid_type(self):
        """Test creating job with invalid type."""
        result = await create_job("test-job", "invalid-type")
        
        assert result["success"] is False
        assert "Invalid job type" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_job_empty_name(self):
        """Test creating job with empty name."""
        result = await create_job("", "freestyle")
        
        assert result["success"] is False
        assert "Job name cannot be empty" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_job_invalid_name_characters(self):
        """Test creating job with invalid characters in name."""
        result = await create_job("job/with/slashes", "freestyle")
        
        assert result["success"] is False
        assert "Invalid characters" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_pipeline_job_without_script(self):
        """Test creating pipeline job without script."""
        result = await create_job("pipeline-job", "pipeline")
        
        assert result["success"] is False
        assert "Pipeline script is required" in result["error"]