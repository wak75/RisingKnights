"""Input validation utilities."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from .exceptions import JenkinsValidationError


class JobName(BaseModel):
    """Validate Jenkins job name."""
    
    name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('name')
    @classmethod
    def validate_job_name(cls, v):
        """Validate job name format."""
        # Jenkins job names cannot contain certain characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f'Job name cannot contain "{char}"')
        
        # Cannot start or end with whitespace
        if v != v.strip():
            raise ValueError('Job name cannot start or end with whitespace')
        
        return v


class BuildNumber(BaseModel):
    """Validate Jenkins build number."""
    
    number: int = Field(..., gt=0)


class NodeName(BaseModel):
    """Validate Jenkins node name."""
    
    name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('name')
    @classmethod
    def validate_node_name(cls, v):
        """Validate node name format."""
        # Similar validation as job names
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f'Node name cannot contain "{char}"')
        
        if v != v.strip():
            raise ValueError('Node name cannot start or end with whitespace')
        
        return v


class PluginName(BaseModel):
    """Validate Jenkins plugin name."""
    
    name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('name')
    @classmethod
    def validate_plugin_name(cls, v):
        """Validate plugin name format."""
        # Plugin names should follow certain patterns
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Plugin name can only contain letters, numbers, dots, underscores, and hyphens')
        
        return v


class Username(BaseModel):
    """Validate Jenkins username."""
    
    username: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        # Username should not contain special characters
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, periods, hyphens, and underscores')
        
        return v


def validate_job_name(name: str) -> str:
    """Validate and return job name."""
    try:
        return JobName(name=name).name
    except Exception as e:
        raise JenkinsValidationError(f"Invalid job name: {e}")


def validate_build_number(number: Any) -> int:
    """Validate and return build number."""
    try:
        if isinstance(number, str):
            number = int(number)
        return BuildNumber(number=number).number
    except Exception as e:
        raise JenkinsValidationError(f"Invalid build number: {e}")


def validate_node_name(name: str) -> str:
    """Validate and return node name."""
    try:
        return NodeName(name=name).name
    except Exception as e:
        raise JenkinsValidationError(f"Invalid node name: {e}")


def validate_plugin_name(name: str) -> str:
    """Validate and return plugin name."""
    try:
        return PluginName(name=name).name
    except Exception as e:
        raise JenkinsValidationError(f"Invalid plugin name: {e}")


def validate_username(username: str) -> str:
    """Validate and return username."""
    try:
        return Username(username=username).username
    except Exception as e:
        raise JenkinsValidationError(f"Invalid username: {e}")


def validate_xml_config(xml_content: str) -> str:
    """Validate XML configuration content."""
    if not xml_content or not xml_content.strip():
        raise JenkinsValidationError("XML content cannot be empty")
    
    # Basic XML validation
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise JenkinsValidationError(f"Invalid XML format: {e}")
    
    return xml_content.strip()


def validate_job_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate job build parameters."""
    if not isinstance(parameters, dict):
        raise JenkinsValidationError("Parameters must be a dictionary")
    
    validated_params = {}
    for key, value in parameters.items():
        if not isinstance(key, str):
            raise JenkinsValidationError("Parameter keys must be strings")
        
        # Convert value to string for Jenkins
        validated_params[key] = str(value) if value is not None else ""
    
    return validated_params


def validate_file_path(path: str) -> str:
    """Validate file path."""
    if not path or not path.strip():
        raise JenkinsValidationError("File path cannot be empty")
    
    # Remove any dangerous path components
    path = path.strip()
    if '..' in path or path.startswith('/'):
        raise JenkinsValidationError("Invalid file path: path traversal not allowed")
    
    return path