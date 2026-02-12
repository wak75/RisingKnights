# Jenkins MCP Server

A comprehensive Model Context Protocol (MCP) server for Jenkins automation using FASTMCP 2.0. This server provides complete Jenkins integration with tools, resources, and prompts for managing Jenkins instances through Claude and other MCP clients.

## 🚀 Features

### Core Capabilities
- **Complete Jenkins Integration**: Full support for all major Jenkins API operations
- **FASTMCP 2.0 Framework**: Built on the latest MCP framework for optimal performance
- **Modular Architecture**: Clean separation of tools, resources, and prompts
- **Type Safety**: Full type hints and validation using Pydantic
- **Rich Logging**: Enhanced logging with Rich for better debugging and monitoring
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Input Validation**: Robust input validation for all operations

### Tools (25+ Available)
- **Job Management**: Create, update, delete, enable/disable Jenkins jobs
- **Build Operations**: Trigger builds, get logs, artifacts, test results
- **Node Management**: Manage Jenkins agents and build nodes
- **Plugin Management**: Install, update, uninstall Jenkins plugins
- **System Operations**: System info, restarts, maintenance mode
- **User Management**: Manage Jenkins users and permissions

### Resources (5 Types)
- **Job Configurations**: Access Jenkins job XML configurations
- **Build Logs**: Formatted console output from builds
- **Build Artifacts**: Download and access build artifacts
- **Workspace Files**: Access files from job workspaces
- **System Metrics**: Jenkins performance and system metrics

### Prompts (15+ Available)
- **Troubleshooting**: Comprehensive error diagnosis and solutions
- **Best Practices**: Jenkins configuration and pipeline best practices
- **Templates**: Pipeline, Job DSL, and deployment templates
- **Security**: Security checklists and compliance guidelines
- **Migration**: Upgrade and migration procedures

### Deployment Options
- **Docker Support**: Complete containerization with multi-stage builds
- **Development Mode**: Hot-reloading and debugging support
- **Production Mode**: Optimized for production with monitoring
- **Claude Desktop**: Easy integration with Claude Desktop app

## 📋 Prerequisites

- **Python 3.9+**: Required for running the MCP server
- **Jenkins Server**: Running Jenkins instance with API access enabled
- **API Token**: Jenkins API token for authentication
- **Docker** (optional): For containerized deployment

## 🛠 Installation

### Method 1: Quick Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd jenkins-mcp-server

# Run the automated setup script
./scripts/setup.sh

# Configure your Jenkins connection
cp env.example .env
# Edit .env with your Jenkins details

# Start the server
./start.sh
```

### Method 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# Install development dependencies (optional)
pip install pytest pytest-asyncio pytest-cov black isort flake8

# Configure environment
cp env.example .env
# Edit .env file with your settings

# Run the server
python -m jenkins_mcp_server.main
```

### Method 3: Docker Deployment

```bash
# Quick deployment
./scripts/deploy.sh

# Development mode with hot-reloading
./scripts/deploy.sh --dev

# Production mode with monitoring
./scripts/deploy.sh --prod
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your Jenkins configuration:

```env
# Jenkins Configuration (Required)
JENKINS_URL=http://localhost:8080
JENKINS_USERNAME=your_username
JENKINS_TOKEN=your_api_token

# Server Configuration (Optional)
SERVER_HOST=localhost
SERVER_PORT=8000
LOG_LEVEL=INFO
DEBUG=false

# Advanced Configuration (Optional)
JENKINS_TIMEOUT=30
JENKINS_VERIFY_SSL=true
```

### Getting Jenkins API Token

1. Navigate to Jenkins → People → [Your Username] → Configure
2. Scroll down to "API Token" section
3. Click "Add new Token" and give it a name
4. Click "Generate" and copy the token
5. Use this token in your `.env` file

## 🔧 Usage

### Claude Desktop Integration

Add to your Claude Desktop configuration file:

**Location**: 
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jenkins-mcp-server": {
      "command": "python",
      "args": ["-m", "jenkins_mcp_server.main"],
      "env": {
        "JENKINS_URL": "http://localhost:8080",
        "JENKINS_USERNAME": "your_username",
        "JENKINS_TOKEN": "your_api_token",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 📚 Available Operations

### Job Management Tools

```python
# Create different types of jobs
create_job(name="my-job", job_type="freestyle", description="My job")
create_job(name="pipeline-job", job_type="pipeline", pipeline_script="...")

# Manage existing jobs
get_job("my-job")                    # Get job information
update_job("my-job", new_config)     # Update job configuration
delete_job("my-job")                 # Delete job
list_jobs(status_filter="success")   # List jobs with filters
enable_job("my-job")                 # Enable disabled job
disable_job("my-job")                # Disable job
```

### Build Operations

```python
# Trigger and manage builds
build_job("my-job", parameters={"BRANCH": "main"})
get_build("my-job", 42)              # Get build #42 info
stop_build("my-job", 42)             # Stop running build
get_build_log("my-job", 42)          # Get console output
list_builds("my-job", limit=10)      # List recent builds
get_build_artifacts("my-job", 42)    # Get build artifacts
get_test_results("my-job", 42)       # Get test results
```

### System Operations

```python
# System management
get_system_info()                    # Get Jenkins system info
get_version_info()                   # Get version details
restart_jenkins()                    # Restart Jenkins safely
quiet_down()                         # Enter maintenance mode
cancel_quiet_down()                  # Exit maintenance mode
run_groovy_script("println 'Hello'") # Execute Groovy script
```

### Resource Access

```python
# Access Jenkins resources through MCP
jenkins://job_config/my-job                    # Job XML configuration
jenkins://build_log/my-job/42                  # Build console output
jenkins://build_artifact/my-job/42/app.jar     # Build artifacts
jenkins://workspace_file/my-job/src/main.py    # Workspace files
jenkins://system_metrics/memory                # System metrics
```

### Prompt Templates

```python
# Get helpful prompts
troubleshoot_jenkins_issue(issue_type="build_failure")
jenkins_best_practices(topic="pipeline_security") 
pipeline_template(type="nodejs", features=["testing", "deployment"])
jenkins_security_checklist()
jenkins_migration_guide()
```

## 🏗 Architecture

### Project Structure

```
jenkins-mcp-server/
├── src/jenkins_mcp_server/          # Main source code
│   ├── main.py                      # Server entry point
│   ├── config.py                    # Configuration management
│   ├── client.py                    # Jenkins API clients
│   ├── tools/                       # MCP tools implementation
│   ├── resources/                   # MCP resources implementation
│   ├── prompts/                     # MCP prompts implementation
│   └── utils/                       # Utility modules
├── tests/                           # Comprehensive test suite
├── scripts/                         # Deployment and setup scripts
├── docs/                            # Documentation
├── Dockerfile                       # Multi-stage Docker build
├── docker-compose.yml               # Basic Docker Compose
├── pyproject.toml                   # Python project configuration
└── README.md                        # This file
```

## 🧪 Development

### Development Setup

```bash
# Setup development environment
./scripts/setup.sh --dev

# Start in development mode
./dev.sh

# Run tests
./test.sh
```

### Testing

```bash
# Run all tests
./test.sh

# Run specific test files
pytest tests/test_config.py -v

# Run with coverage
pytest --cov=jenkins_mcp_server --cov-report=html
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Start with Docker Compose
docker-compose up -d

# Deploy with script
./scripts/deploy.sh
```

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Full documentation available
- **Community**: Discussions and support

---

## 🎯 Quick Start Summary

```bash
git clone <repo> && cd jenkins-mcp-server
./scripts/setup.sh
cp env.example .env  # Edit with your Jenkins details
./start.sh
```

Then add to Claude Desktop config and start automating your Jenkins! 🚀