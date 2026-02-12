"""Configuration management for Kubernetes MCP Server."""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class KubernetesConfig(BaseModel):
    """Kubernetes connection configuration."""
    
    kubeconfig: Optional[str] = Field(None, description="Path to kubeconfig file")
    context: Optional[str] = Field(None, description="Kubernetes context to use")
    namespace: str = Field("default", description="Default namespace")
    timeout: int = Field(30, description="Request timeout in seconds")
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class ServerConfig(BaseSettings):
    """Main server configuration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )
    
    # Kubernetes configuration
    kubeconfig: Optional[str] = Field(default=None, validation_alias='KUBECONFIG')
    kube_context: Optional[str] = Field(default=None, validation_alias='KUBE_CONTEXT')
    kube_namespace: str = Field(default="default", validation_alias='KUBE_NAMESPACE')
    timeout: int = Field(default=30, validation_alias='TIMEOUT')
    
    # Server configuration
    host: str = Field(default="0.0.0.0", validation_alias='SERVER_HOST')
    port: int = Field(default=8001, validation_alias='SERVER_PORT')
    transport: str = Field(default="sse", validation_alias='TRANSPORT')
    log_level: str = Field(default="INFO", validation_alias='LOG_LEVEL')
    debug: bool = Field(default=False, validation_alias='DEBUG')
    
    # Resource limits
    max_log_lines: int = Field(default=1000, validation_alias='MAX_LOG_LINES')
    
    @property
    def kubernetes_config(self) -> KubernetesConfig:
        """Get Kubernetes configuration."""
        return KubernetesConfig(
            kubeconfig=self.kubeconfig,
            context=self.kube_context,
            namespace=self.kube_namespace,
            timeout=self.timeout,
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