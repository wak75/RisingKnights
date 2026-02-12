"""Test configuration and fixtures."""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import json

from jenkins_mcp_server.config import JenkinsConfig, ServerConfig
from jenkins_mcp_server.client import AsyncJenkinsClient


@pytest.fixture
def jenkins_config():
    """Create a test Jenkins configuration."""
    return JenkinsConfig(
        url="http://localhost:8080",
        username="test_user",
        token="test_token"
    )


@pytest.fixture
def server_config():
    """Create a test server configuration."""
    return ServerConfig(
        host="localhost",
        port=8000,
        log_level="DEBUG",
        debug=True
    )


@pytest.fixture
def mock_jenkins_client():
    """Create a mock Jenkins client."""
    client = Mock(spec=AsyncJenkinsClient)
    
    # Mock common methods
    client.get_job_info = AsyncMock()
    client.create_job = AsyncMock()
    client.delete_job = AsyncMock()
    client.build_job = AsyncMock()
    client.get_build_info = AsyncMock()
    client.get_build_console_output = AsyncMock()
    client.get_nodes = AsyncMock()
    client.get_plugins = AsyncMock()
    client.get_system_info = AsyncMock()
    client.get_users = AsyncMock()
    
    return client


@pytest.fixture
def sample_job_config():
    """Sample Jenkins job configuration XML."""
    return """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test job</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "Hello, World!"</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>"""


@pytest.fixture
def sample_job_info():
    """Sample Jenkins job information."""
    return {
        "name": "test-job",
        "displayName": "Test Job",
        "description": "A test job",
        "buildable": True,
        "builds": [
            {"number": 1, "url": "http://localhost:8080/job/test-job/1/"},
            {"number": 2, "url": "http://localhost:8080/job/test-job/2/"}
        ],
        "lastBuild": {"number": 2, "url": "http://localhost:8080/job/test-job/2/"},
        "lastCompletedBuild": {"number": 2, "url": "http://localhost:8080/job/test-job/2/"},
        "lastSuccessfulBuild": {"number": 2, "url": "http://localhost:8080/job/test-job/2/"},
        "nextBuildNumber": 3,
        "inQueue": False,
        "color": "blue"
    }


@pytest.fixture
def sample_build_info():
    """Sample Jenkins build information."""
    return {
        "number": 1,
        "displayName": "#1",
        "description": None,
        "building": False,
        "duration": 5000,
        "estimatedDuration": 5000,
        "result": "SUCCESS",
        "timestamp": 1640995200000,
        "url": "http://localhost:8080/job/test-job/1/",
        "artifacts": [
            {
                "fileName": "output.txt",
                "relativePath": "output.txt",
                "displayPath": "output.txt"
            }
        ],
        "actions": [],
        "changeSet": {"items": [], "kind": "git"}
    }


@pytest.fixture
def sample_console_output():
    """Sample Jenkins build console output."""
    return """Started by user admin
Running in Durability level: MAX_SURVIVABILITY
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/test-job
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Build)
[Pipeline] echo
Hello, World!
[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
Finished: SUCCESS"""


@pytest.fixture
def sample_node_info():
    """Sample Jenkins node information."""
    return {
        "displayName": "master",
        "description": "the master Jenkins node",
        "executors": [{"currentExecutable": None, "idle": True, "likelyStuck": False, "number": 0, "progress": -1}],
        "icon": "computer.png",
        "iconClassName": "icon-computer",
        "idle": True,
        "jnlpAgent": False,
        "launchSupported": True,
        "loadStatistics": {},
        "manualLaunchAllowed": True,
        "monitorData": {
            "hudson.node_monitors.SwapSpaceMonitor": {
                "availablePhysicalMemory": 8589934592,
                "availableSwapSpace": 2147483648,
                "totalPhysicalMemory": 17179869184,
                "totalSwapSpace": 4294967296
            }
        },
        "numExecutors": 2,
        "offline": False,
        "offlineCause": None,
        "offlineCauseReason": "",
        "oneOffExecutors": [],
        "temporarilyOffline": False
    }


@pytest.fixture
def sample_plugin_info():
    """Sample Jenkins plugin information."""
    return [
        {
            "shortName": "build-timeout",
            "displayName": "Build Timeout",
            "version": "1.27",
            "enabled": True,
            "active": True,
            "hasUpdate": False,
            "bundled": False
        },
        {
            "shortName": "ant",
            "displayName": "Ant Plugin",
            "version": "1.13",
            "enabled": True,
            "active": True,
            "hasUpdate": True,
            "bundled": False
        }
    ]


@pytest.fixture
def sample_system_info():
    """Sample Jenkins system information."""
    return {
        "hudson.model.Hudson": {
            "Jenkins": "2.426.1",
            "jenkins.model.Jenkins.version": "2.426.1"
        },
        "hudson.node_monitors.ArchitectureMonitor": "Linux (amd64)",
        "hudson.node_monitors.ClockMonitor": 0,
        "hudson.node_monitors.DiskSpaceMonitor": "/var/jenkins_home: 95.12 GB",
        "hudson.node_monitors.ResponseTimeMonitor": {
            "average": 100
        },
        "hudson.node_monitors.SwapSpaceMonitor": {
            "availablePhysicalMemory": 8589934592,
            "availableSwapSpace": 2147483648,
            "totalPhysicalMemory": 17179869184,
            "totalSwapSpace": 4294967296
        },
        "hudson.node_monitors.TemporarySpaceMonitor": "/tmp: 10.5 GB"
    }


@pytest.fixture
def sample_user_info():
    """Sample Jenkins user information."""
    return [
        {
            "user": {
                "id": "admin",
                "fullName": "Administrator",
                "description": "System Administrator",
                "properties": []
            }
        },
        {
            "user": {
                "id": "developer",
                "fullName": "Developer User",
                "description": "Development team member",
                "properties": []
            }
        }
    ]


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Create some sample files
    (workspace / "test.txt").write_text("Hello from workspace")
    (workspace / "build.log").write_text("Build started\nBuild completed successfully")
    
    subdir = workspace / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file content")
    
    return workspace


@pytest.fixture
def mock_fastmcp():
    """Create a mock FastMCP instance."""
    mock_mcp = Mock()
    mock_mcp.tool = Mock()
    mock_mcp.resource = Mock()
    mock_mcp.prompt = Mock()
    return mock_mcp


@pytest.fixture
def env_vars():
    """Set up test environment variables."""
    test_env = {
        "JENKINS_URL": "http://localhost:8080",
        "JENKINS_USERNAME": "test_user",
        "JENKINS_TOKEN": "test_token",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true"
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
def cleanup_files():
    """Clean up test files after tests."""
    files_to_cleanup = []
    
    def register_file(filepath):
        files_to_cleanup.append(filepath)
    
    yield register_file
    
    # Cleanup
    for filepath in files_to_cleanup:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            pass


class AsyncContextManager:
    """Helper class for testing async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Create an async context manager for testing."""
    return AsyncContextManager


# Test data for various scenarios
TEST_JOB_CONFIGS = {
    "freestyle": {
        "job_type": "freestyle",
        "config": """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Freestyle test job</description>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "Freestyle job executed"</command>
    </hudson.tasks.Shell>
  </builders>
</project>"""
    },
    "pipeline": {
        "job_type": "pipeline",
        "config": """<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <description>Pipeline test job</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                echo 'Pipeline job executed'
            }
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""
    }
}

TEST_BUILD_PARAMETERS = {
    "simple": {"BRANCH": "main"},
    "complex": {
        "BRANCH": "develop",
        "DEPLOY_ENV": "staging",
        "RUN_TESTS": "true",
        "NOTIFICATION_EMAIL": "test@example.com"
    }
}

TEST_ERROR_RESPONSES = {
    "job_not_found": {
        "status_code": 404,
        "message": "No such job: non-existent-job"
    },
    "permission_denied": {
        "status_code": 403,
        "message": "Access Denied: admin is missing the Job/Configure permission"
    },
    "server_error": {
        "status_code": 500,
        "message": "Internal server error"
    }
}