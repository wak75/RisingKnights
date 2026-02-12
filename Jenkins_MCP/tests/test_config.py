"""Tests for Jenkins MCP Server configuration."""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from jenkins_mcp_server.config import JenkinsConfig, ServerConfig


class TestJenkinsConfig:
    """Test Jenkins configuration."""
    
    def test_jenkins_config_creation(self):
        """Test creating Jenkins configuration."""
        config = JenkinsConfig(
            url="http://localhost:8080",
            username="admin",
            token="secret"
        )
        
        assert config.url == "http://localhost:8080"
        assert config.username == "admin"
        assert config.token == "secret"
        assert config.timeout == 30
        assert config.verify_ssl is True
    
    def test_jenkins_config_from_env(self):
        """Test creating Jenkins configuration from environment variables."""
        env_vars = {
            "JENKINS_URL": "http://test.jenkins.com",
            "JENKINS_USERNAME": "testuser",
            "JENKINS_TOKEN": "testtoken",
            "JENKINS_TIMEOUT": "60",
            "JENKINS_VERIFY_SSL": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            config = JenkinsConfig()
            
            assert config.url == "http://test.jenkins.com"
            assert config.username == "testuser"
            assert config.token == "testtoken"
            assert config.timeout == 60
            assert config.verify_ssl is False
    
    def test_jenkins_config_validation_missing_url(self):
        """Test validation error when URL is missing."""
        with pytest.raises(ValidationError) as exc_info:
            JenkinsConfig(username="admin", token="secret")
        
        assert "url" in str(exc_info.value)
    
    def test_jenkins_config_validation_invalid_url(self):
        """Test validation error with invalid URL."""
        with pytest.raises(ValidationError):
            JenkinsConfig(
                url="invalid-url",
                username="admin",
                token="secret"
            )
    
    def test_jenkins_config_url_normalization(self):
        """Test URL normalization (removing trailing slash)."""
        config = JenkinsConfig(
            url="http://localhost:8080/",
            username="admin",
            token="secret"
        )
        
        assert config.url == "http://localhost:8080"
    
    def test_jenkins_config_timeout_validation(self):
        """Test timeout validation."""
        with pytest.raises(ValidationError):
            JenkinsConfig(
                url="http://localhost:8080",
                username="admin",
                token="secret",
                timeout=-1
            )


class TestServerConfig:
    """Test server configuration."""
    
    def test_server_config_creation(self):
        """Test creating server configuration."""
        config = ServerConfig(
            host="0.0.0.0",
            port=8000,
            log_level="INFO",
            debug=False
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.log_level == "INFO"
        assert config.debug is False
    
    def test_server_config_from_env(self):
        """Test creating server configuration from environment variables."""
        env_vars = {
            "SERVER_HOST": "127.0.0.1",
            "SERVER_PORT": "9000",
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = ServerConfig()
            
            assert config.host == "127.0.0.1"
            assert config.port == 9000
            assert config.log_level == "DEBUG"
            assert config.debug is True
    
    def test_server_config_defaults(self):
        """Test server configuration defaults."""
        config = ServerConfig()
        
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.log_level == "INFO"
        assert config.debug is False
    
    def test_server_config_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValidationError):
            ServerConfig(port=0)
        
        with pytest.raises(ValidationError):
            ServerConfig(port=70000)
    
    def test_server_config_log_level_validation(self):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            config = ServerConfig(log_level=level)
            assert config.log_level == level
        
        with pytest.raises(ValidationError):
            ServerConfig(log_level="INVALID")


class TestConfigIntegration:
    """Test configuration integration scenarios."""
    
    def test_complete_config_from_env(self):
        """Test complete configuration from environment."""
        env_vars = {
            "JENKINS_URL": "http://ci.company.com",
            "JENKINS_USERNAME": "ci-user",
            "JENKINS_TOKEN": "ci-token",
            "JENKINS_TIMEOUT": "45",
            "SERVER_HOST": "0.0.0.0",
            "SERVER_PORT": "8080",
            "LOG_LEVEL": "WARNING",
            "DEBUG": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            jenkins_config = JenkinsConfig()
            server_config = ServerConfig()
            
            # Verify Jenkins config
            assert jenkins_config.url == "http://ci.company.com"
            assert jenkins_config.username == "ci-user"
            assert jenkins_config.token == "ci-token"
            assert jenkins_config.timeout == 45
            
            # Verify server config
            assert server_config.host == "0.0.0.0"
            assert server_config.port == 8080
            assert server_config.log_level == "WARNING"
            assert server_config.debug is False
    
    def test_mixed_config_sources(self):
        """Test mixing environment variables and direct parameters."""
        env_vars = {
            "JENKINS_URL": "http://env.jenkins.com",
            "SERVER_HOST": "env.host.com"
        }
        
        with patch.dict(os.environ, env_vars):
            # Override some values directly
            jenkins_config = JenkinsConfig(
                username="direct-user",
                token="direct-token"
            )
            server_config = ServerConfig(port=9999)
            
            # Should use env for URL and host
            assert jenkins_config.url == "http://env.jenkins.com"
            assert server_config.host == "env.host.com"
            
            # Should use direct values
            assert jenkins_config.username == "direct-user"
            assert jenkins_config.token == "direct-token"
            assert server_config.port == 9999