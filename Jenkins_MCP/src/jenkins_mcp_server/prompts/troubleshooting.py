"""Jenkins troubleshooting prompts."""

from typing import Any, Dict, List, Optional


def register_prompts(mcp):
    """Register troubleshooting prompts with the MCP server."""
    
    @mcp.prompt("jenkins_troubleshoot_build_failure")
    async def troubleshoot_build_failure() -> str:
        """
        Provide comprehensive guidance for troubleshooting Jenkins build failures.
        
        Returns:
            Detailed troubleshooting guide for build failures
        """
        return """# Jenkins Build Failure Troubleshooting Guide

## Initial Investigation Steps

### 1. Check Build Status and Result
- Navigate to the failed build: Job → Build #X
- Review the build result (FAILURE, ABORTED, UNSTABLE)
- Note the build duration and compare with typical builds

### 2. Console Output Analysis
- Click "Console Output" for the failed build
- Look for ERROR, FAILED, or Exception messages
- Check the last 50-100 lines for immediate error causes
- Search for keywords: "BUILD FAILED", "Error:", "Exception:"

### 3. Build Environment Check
```groovy
// Add this to your pipeline for environment debugging
stage('Debug Environment') {
    steps {
        sh 'env | sort'
        sh 'java -version'
        sh 'mvn --version' // or your build tool
        sh 'pwd && ls -la'
    }
}
```

## Common Build Failure Patterns

### Compilation Errors
**Symptoms:** "compilation failed", "cannot find symbol"
**Solutions:**
- Check for missing dependencies in pom.xml/build.gradle
- Verify Java version compatibility
- Look for recent code changes that might have introduced errors
- Check if all required libraries are available

### Test Failures
**Symptoms:** "Tests run: X, Failures: Y", "AssertionError"
**Solutions:**
- Review test output for specific failing tests
- Check if tests are environment-dependent
- Verify test data availability
- Consider if tests need to be updated after recent changes

### SCM/Git Issues
**Symptoms:** "Failed to connect to repository", "Authentication failed"
**Solutions:**
- Check Jenkins credentials for Git access
- Verify repository URL is correct
- Test Git connectivity from Jenkins node
- Check if repository has been moved or renamed

### Workspace Issues
**Symptoms:** "No space left on device", "Permission denied"
**Solutions:**
- Check disk space on Jenkins nodes
- Clean up old workspaces: Jenkins → Manage → Disk Usage
- Verify file permissions in workspace
- Consider using workspace cleanup plugins

### Network/Connectivity Issues
**Symptoms:** "Connection timed out", "Host unreachable"
**Solutions:**
- Check network connectivity from Jenkins nodes
- Verify firewall rules
- Test dependency repository accessibility
- Check proxy settings if applicable

## Advanced Troubleshooting

### Node-Specific Issues
1. Check if failure occurs on specific nodes only
2. Compare node configurations and installed software
3. Verify node labels and restrictions
4. Test builds on different nodes

### Pipeline-Specific Debugging
```groovy
// Add error handling to your pipeline
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                script {
                    try {
                        // Your build steps
                        sh 'mvn clean compile'
                    } catch (Exception e) {
                        echo "Build failed with error: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Build step failed")
                    }
                }
            }
        }
    }
    post {
        failure {
            echo "Build failed. Environment info:"
            sh 'env | sort'
            archiveArtifacts artifacts: '**/target/surefire-reports/*.xml', allowEmptyArchive: true
        }
    }
}
```

### Resource Monitoring
- Check CPU and memory usage during builds
- Monitor disk I/O for slow operations
- Review Jenkins system log for system-level errors

## Prevention Strategies

### 1. Build Health Monitoring
- Set up build notifications (email, Slack, etc.)
- Use build status badges in repositories
- Monitor build trends and failure patterns

### 2. Environment Consistency
- Use Docker containers for consistent environments
- Pin dependency versions
- Document environment requirements

### 3. Test Quality
- Implement proper unit and integration tests
- Use test reports and coverage analysis
- Keep tests independent and deterministic

### 4. Regular Maintenance
- Keep Jenkins and plugins updated
- Clean up old builds and workspaces regularly
- Monitor system resources and capacity

## Quick Commands for Investigation

```bash
# Check Jenkins logs
tail -f /var/log/jenkins/jenkins.log

# Check disk usage
df -h
du -sh /var/jenkins_home/workspace/*

# Check running processes
ps aux | grep jenkins

# Test network connectivity
curl -I https://repo1.maven.org/maven2/
ping github.com

# Check Git connectivity
git ls-remote <repository-url>
```

## Getting Help

1. **Jenkins Documentation**: Check official Jenkins docs for your specific issue
2. **Community Forums**: Post detailed error information on Jenkins community forums
3. **Stack Overflow**: Search for similar error messages and solutions
4. **Plugin Documentation**: Review documentation for specific plugins causing issues

Remember: Always provide specific error messages, Jenkins version, plugin versions, and environment details when seeking help.
"""
    
    @mcp.prompt("jenkins_troubleshoot_performance")
    async def troubleshoot_performance() -> str:
        """
        Provide guidance for troubleshooting Jenkins performance issues.
        
        Returns:
            Detailed performance troubleshooting guide
        """
        return """# Jenkins Performance Troubleshooting Guide

## Performance Issue Identification

### Build Performance Issues
**Symptoms:**
- Builds taking significantly longer than usual
- Builds timing out
- Queue items waiting too long to start

**Quick Assessment:**
1. Compare current build times with historical data
2. Check if issue affects all jobs or specific ones
3. Identify if problem started after specific changes
4. Monitor resource usage during builds

### UI/Web Interface Performance
**Symptoms:**
- Slow page loading
- Timeouts accessing Jenkins web interface  
- Unresponsive UI elements

### System Resource Issues
**Symptoms:**
- High CPU usage
- Memory warnings or OutOfMemory errors
- Disk I/O bottlenecks
- Network connectivity issues

## System-Level Troubleshooting

### Memory Analysis
```bash
# Check Jenkins JVM memory usage
jps -v | grep jenkins

# Monitor memory usage
free -h
top -p <jenkins-pid>

# Analyze garbage collection
jstat -gc <jenkins-pid> 5s
```

**Memory Optimization:**
```bash
# Recommended JVM settings for Jenkins
-Xms2g -Xmx8g
-XX:+UseG1GC
-XX:+UseStringDeduplication
-XX:MaxGCPauseMillis=100
-XX:+UnlockExperimentalVMOptions
-XX:+UseCGroupMemoryLimitForHeap
```

### CPU Performance
```bash
# Check CPU usage
htop
iostat -x 1

# Profile Java process
perf record -p <jenkins-pid> sleep 30
perf report
```

### Disk I/O Analysis
```bash
# Check disk usage and performance
df -h
iotop
lsof +D /var/jenkins_home
```

## Jenkins-Specific Optimizations

### Build Performance
1. **Parallel Builds:**
```groovy
pipeline {
    agent none
    stages {
        stage('Parallel Tests') {
            parallel {
                stage('Unit Tests') {
                    agent any
                    steps { sh 'mvn test' }
                }
                stage('Integration Tests') {
                    agent any
                    steps { sh 'mvn verify' }
                }
            }
        }
    }
}
```

2. **Build Caching:**
- Use Maven/Gradle build caches
- Cache Docker layers
- Reuse workspaces when possible

3. **Node Optimization:**
- Distribute builds across multiple nodes
- Use appropriate node labels
- Configure adequate executors per node

### Plugin Performance
**Heavy Plugins to Monitor:**
- Blue Ocean (can impact UI performance)
- Build Pipeline Plugin
- Heavy reporting plugins

**Plugin Optimization:**
1. Disable unused plugins
2. Update plugins regularly
3. Review plugin-specific performance settings
4. Consider lightweight alternatives

### Database Optimization (if using external DB)
```sql
-- PostgreSQL optimization examples
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Analyze table performance
ANALYZE builds;
ANALYZE jobs;
```

## Build Optimization Strategies

### Pipeline Efficiency
```groovy
pipeline {
    agent {
        label 'fast-node'
    }
    options {
        // Skip default checkout to optimize
        skipDefaultCheckout(true)
        // Set build timeout
        timeout(time: 30, unit: 'MINUTES')
        // Limit build history
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    stages {
        stage('Optimized Checkout') {
            steps {
                // Shallow clone for faster checkout
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [[$class: 'CloneOption', 
                                 shallow: true, depth: 1]],
                    userRemoteConfigs: [[url: env.GIT_URL]]
                ])
            }
        }
    }
}
```

### Workspace Management
```groovy
// Clean workspace efficiently
pipeline {
    agent any
    options {
        // Clean workspace before build
        skipDefaultCheckout(true)
    }
    stages {
        stage('Clean Setup') {
            steps {
                // Custom cleanup
                sh 'find . -name "*.tmp" -delete'
                checkout scm
            }
        }
    }
    post {
        always {
            // Clean specific directories only
            sh 'rm -rf target/ node_modules/'
        }
    }
}
```

## Monitoring and Alerting

### Key Metrics to Monitor
1. **Build Metrics:**
   - Average build duration
   - Build queue length
   - Build success rate
   - Node utilization

2. **System Metrics:**
   - Memory usage
   - CPU utilization
   - Disk I/O
   - Network throughput

3. **Jenkins Metrics:**
   - Active sessions
   - Plugin performance
   - HTTP response times

### Monitoring Setup
```groovy
// Add performance monitoring to builds
pipeline {
    agent any
    stages {
        stage('Performance Monitor') {
            steps {
                script {
                    def startTime = System.currentTimeMillis()
                    
                    // Your build steps here
                    sh 'mvn clean install'
                    
                    def duration = System.currentTimeMillis() - startTime
                    echo "Build completed in ${duration}ms"
                    
                    // Alert if build takes too long
                    if (duration > 600000) { // 10 minutes
                        echo "WARNING: Build took longer than expected"
                    }
                }
            }
        }
    }
}
```

## Quick Performance Fixes

### Immediate Actions
1. **Restart Jenkins** (if memory issues)
2. **Clear build queue** (if backed up)
3. **Disable problematic plugins** temporarily
4. **Add more executors** if CPU allows
5. **Clean old builds** to free disk space

### Configuration Tuning
```bash
# Jenkins system properties for performance
-Djenkins.model.Jenkins.buildsDir=/fast-storage/builds
-Djenkins.model.Jenkins.workspacesDir=/fast-storage/workspaces
-Dhudson.model.DirectoryBrowserSupport.CSP=
-Djenkins.install.runSetupWizard=false
```

## Long-term Performance Strategy

### Infrastructure Planning
1. **Scale horizontally** with more nodes
2. **Use SSD storage** for Jenkins home
3. **Implement load balancing** for UI
4. **Database optimization** for large installations

### Regular Maintenance
1. **Weekly:** Clean old builds and logs
2. **Monthly:** Review plugin usage and updates
3. **Quarterly:** Analyze performance trends
4. **Annually:** Review infrastructure capacity

### Best Practices
- Keep Jenkins and plugins updated
- Use pipeline as code for consistency
- Implement proper backup strategies
- Monitor key performance indicators
- Document performance baselines

Remember: Performance optimization is iterative. Make one change at a time and measure the impact before proceeding with additional changes.
"""
    
    @mcp.prompt("jenkins_troubleshoot_connectivity")
    async def troubleshoot_connectivity() -> str:
        """
        Provide guidance for troubleshooting Jenkins connectivity issues.
        
        Returns:
            Detailed connectivity troubleshooting guide
        """
        return """# Jenkins Connectivity Troubleshooting Guide

## Common Connectivity Issues

### 1. Jenkins Web Interface Not Accessible
**Symptoms:**
- Cannot access Jenkins URL
- Connection timeout or refused
- 502/503 gateway errors

**Troubleshooting Steps:**
```bash
# Check if Jenkins service is running
systemctl status jenkins
# or
service jenkins status

# Check if Jenkins is listening on correct port
netstat -tulpn | grep :8080
ss -tulpn | grep :8080

# Test local connectivity
curl -I http://localhost:8080
wget --spider http://localhost:8080
```

### 2. Git/SCM Connectivity Issues
**Symptoms:**
- "Failed to connect to repository"
- "Authentication failed"
- "Host key verification failed"

**Solutions:**
```bash
# Test Git connectivity from Jenkins user
sudo -u jenkins git ls-remote <repository-url>

# Check SSH key setup
sudo -u jenkins ssh -T git@github.com
sudo -u jenkins ssh -vT git@github.com  # verbose mode

# Test HTTPS Git access
sudo -u jenkins git clone <https-repo-url> /tmp/test-clone
```

### 3. Node/Agent Connectivity
**Symptoms:**
- Agents showing as offline
- "Channel is already closed" errors
- Agent launch failures

**Troubleshooting:**
```bash
# Check network connectivity to agent
ping <agent-hostname>
telnet <agent-hostname> <agent-port>

# Test SSH connectivity (for SSH agents)
ssh -i /var/jenkins_home/.ssh/id_rsa jenkins@<agent-hostname>

# Check firewall rules
iptables -L -n
ufw status
```

## Network Configuration

### Firewall and Security Groups
**Required Ports:**
- **8080**: Jenkins web interface (default)
- **50000**: Agent communication (default)
- **22**: SSH for SSH-based agents
- **80/443**: If using reverse proxy

**Firewall Configuration:**
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 8080
sudo ufw allow 50000
sudo ufw allow ssh

# CentOS/RHEL (firewalld)
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=50000/tcp
firewall-cmd --reload

# iptables
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 50000 -j ACCEPT
```

### Proxy Configuration
**HTTP Proxy Setup:**
```bash
# Jenkins system properties
-Dhttp.proxyHost=proxy.company.com
-Dhttp.proxyPort=8080
-Dhttps.proxyHost=proxy.company.com
-Dhttps.proxyPort=8080
-Dhttp.nonProxyHosts="localhost|127.*|[::1]|*.company.com"
```

**Jenkins Proxy Configuration:**
1. Go to "Manage Jenkins" → "Manage Plugins" → "Advanced"
2. Configure HTTP Proxy settings
3. Test connection using "Validate HTTP proxy"

## Authentication Issues

### LDAP/Active Directory
**Common Issues:**
- Connection timeout to LDAP server
- Authentication failures
- Group membership not working

**Debugging:**
```bash
# Test LDAP connectivity
ldapsearch -x -H ldap://ldap.company.com:389 -D "cn=jenkins,ou=service,dc=company,dc=com" -W

# Test LDAP user lookup
ldapsearch -x -H ldap://ldap.company.com:389 -D "cn=jenkins,ou=service,dc=company,dc=com" -W -b "dc=company,dc=com" "(uid=username)"
```

**Configuration Check:**
1. Verify LDAP server URL and port
2. Check bind DN and password
3. Validate user and group search bases
4. Test with LDAP browser tool

### GitHub/GitLab Integration
**OAuth Issues:**
```bash
# Check OAuth app configuration
# Verify callback URLs match Jenkins URL
# Test token permissions

# For GitHub:
curl -H "Authorization: token <github-token>" https://api.github.com/user

# For GitLab:
curl -H "Private-Token: <gitlab-token>" https://gitlab.com/api/v4/user
```

## DNS and Name Resolution

### DNS Troubleshooting
```bash
# Test DNS resolution
nslookup jenkins.company.com
dig jenkins.company.com

# Check /etc/hosts file
cat /etc/hosts

# Test reverse DNS
nslookup <jenkins-ip>
```

### Host File Configuration
```bash
# Add entries to /etc/hosts if needed
echo "192.168.1.100 jenkins.local" >> /etc/hosts
echo "192.168.1.101 agent1.local" >> /etc/hosts
```

## SSL/TLS Issues

### Certificate Problems
**Symptoms:**
- "SSL certificate problem"
- "self signed certificate"
- "certificate verify failed"

**Solutions:**
```bash
# Check certificate validity
openssl s_client -connect jenkins.company.com:443 -servername jenkins.company.com

# Add certificate to Java truststore
keytool -import -alias jenkins-cert -file jenkins.crt -keystore $JAVA_HOME/jre/lib/security/cacerts

# Disable SSL verification (not recommended for production)
git config --global http.sslVerify false
```

### HTTPS Configuration
```bash
# Generate self-signed certificate for testing
keytool -genkey -keyalg RSA -alias jenkins -keystore jenkins.jks -storepass changeit -keysize 2048

# Start Jenkins with HTTPS
java -jar jenkins.war --httpPort=-1 --httpsPort=8443 --httpsKeyStore=jenkins.jks --httpsKeyStorePassword=changeit
```

## Reverse Proxy Issues

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name jenkins.company.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName jenkins.company.com
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass / http://localhost:8080/
    ProxyPassReverse / http://localhost:8080/
    
    # Headers for Jenkins
    ProxyPassReverse / http://localhost:8080/
    ProxyPassReverse / http://jenkins.company.com/
</VirtualHost>
```

## Agent-Specific Connectivity

### SSH Agents
```bash
# Generate SSH key for Jenkins
sudo -u jenkins ssh-keygen -t rsa -b 4096 -C "jenkins@company.com"

# Copy public key to agent
sudo -u jenkins ssh-copy-id jenkins@agent-hostname

# Test SSH connection
sudo -u jenkins ssh jenkins@agent-hostname 'echo "Connection successful"'
```

### JNLP Agents
**Connection Issues:**
1. Check agent secret matches
2. Verify Jenkins URL is accessible from agent
3. Check Java version compatibility
4. Test network connectivity on port 50000

```bash
# Download and run JNLP agent
wget http://jenkins.company.com:8080/jnlpJars/agent.jar
java -jar agent.jar -jnlpUrl http://jenkins.company.com:8080/computer/AgentName/slave-agent.jnlp -secret <secret>
```

## Monitoring and Logging

### Enable Debug Logging
1. Go to "Manage Jenkins" → "System Log"
2. Add new log recorder
3. Set logger levels:
   - `hudson.remoting`: ALL (for agent issues)
   - `org.eclipse.jgit`: ALL (for Git issues)
   - `jenkins.security`: ALL (for auth issues)

### Network Monitoring Tools
```bash
# Monitor network connections
netstat -an | grep :8080
ss -tuln | grep :8080

# Capture network traffic
tcpdump -i eth0 port 8080
wireshark  # GUI tool for packet analysis

# Check network latency
mtr jenkins.company.com
traceroute jenkins.company.com
```

## Quick Diagnostics Script
```bash
#!/bin/bash
echo "=== Jenkins Connectivity Diagnostics ==="
echo "Date: $(date)"
echo

echo "1. Service Status:"
systemctl status jenkins | head -10

echo -e "\n2. Port Listening:"
netstat -tulpn | grep -E ":(8080|50000)"

echo -e "\n3. Disk Space:"
df -h | grep -E "(Filesystem|jenkins|home)"

echo -e "\n4. Memory Usage:"
free -h

echo -e "\n5. Recent Logs:"
tail -20 /var/log/jenkins/jenkins.log

echo -e "\n6. Network Connectivity Test:"
curl -I -s -o /dev/null -w "HTTP Status: %{http_code}, Total Time: %{time_total}s\n" http://localhost:8080
```

## Prevention and Best Practices

1. **Regular Monitoring**: Set up monitoring for Jenkins services and connectivity
2. **Documentation**: Maintain network diagrams and configuration documentation
3. **Backup Configurations**: Regular backup of Jenkins configuration and certificates
4. **Security Updates**: Keep Jenkins and system packages updated
5. **Network Redundancy**: Consider multiple network paths and load balancing
6. **Automated Testing**: Implement connectivity tests as part of maintenance procedures

Remember: Always test connectivity changes in a non-production environment first, and have rollback procedures in place.
"""