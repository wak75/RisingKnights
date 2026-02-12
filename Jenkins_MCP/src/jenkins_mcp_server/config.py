"""Configuration management for Jenkins MCP Server."""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class JenkinsConfig(BaseModel):
    """Jenkins connection configuration."""
    
    url: str = Field(..., description="Jenkins server URL")
    username: Optional[str] = Field(None, description="Jenkins username")
    token: Optional[str] = Field(None, description="Jenkins API token")
    password: Optional[str] = Field(None, description="Jenkins password")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum connection retries")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate Jenkins URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Jenkins URL must start with http:// or https://')
        return v.rstrip('/')
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries value."""
        if v < 0:
            raise ValueError('Max retries must be non-negative')
        return v


class ServerConfig(BaseSettings):
    """Main server configuration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'  # Ignore extra fields for now
    )
    
    # Jenkins configuration
    jenkins_url: str = Field(default="http://localhost:8080", validation_alias='JENKINS_URL')
    jenkins_username: Optional[str] = Field(default=None, validation_alias='JENKINS_USERNAME')
    jenkins_token: Optional[str] = Field(default=None, validation_alias='JENKINS_TOKEN')
    jenkins_password: Optional[str] = Field(default=None, validation_alias='JENKINS_PASSWORD')
    jenkins_timeout: int = Field(default=30, validation_alias='JENKINS_TIMEOUT')
    jenkins_max_retries: int = Field(default=3, validation_alias='JENKINS_MAX_RETRIES')
    jenkins_verify_ssl: bool = Field(default=True, validation_alias='JENKINS_VERIFY_SSL')
    
    # Server configuration
    host: str = Field(default="0.0.0.0", validation_alias='SERVER_HOST')
    port: int = Field(default=8000, validation_alias='SERVER_PORT')
    transport: str = Field(default="sse", validation_alias='TRANSPORT')
    log_level: str = Field(default="INFO", validation_alias='LOG_LEVEL')
    debug: bool = Field(default=False, validation_alias='DEBUG')
    
    # Resource limits
    max_log_lines: int = Field(default=1000, validation_alias='MAX_LOG_LINES')
    max_artifact_size: int = Field(default=100 * 1024 * 1024, validation_alias='MAX_ARTIFACT_SIZE')  # 100MB
    
    @property
    def jenkins_config(self) -> JenkinsConfig:
        """Get Jenkins configuration."""
        return JenkinsConfig(
            url=self.jenkins_url,
            username=self.jenkins_username,
            token=self.jenkins_token,
            password=self.jenkins_password,
            timeout=self.jenkins_timeout,
            max_retries=self.jenkins_max_retries,
            verify_ssl=self.jenkins_verify_ssl,
        )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()


# Global configuration instance
config = ServerConfig()