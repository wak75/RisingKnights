"""Jenkins best practices prompts."""


def register_prompts(mcp):
    """Register best practices prompts with the MCP server."""
    
    @mcp.prompt("jenkins_security_best_practices")
    async def security_best_practices() -> str:
        """
        Provide comprehensive Jenkins security best practices.
        
        Returns:
            Detailed security best practices guide
        """
        return """# Jenkins Security Best Practices

## Authentication and Authorization

### 1. Enable Security
- Always enable Jenkins security (never run with security disabled)
- Use "Manage Jenkins" → "Configure Global Security"
- Choose appropriate security realm (LDAP, Active Directory, etc.)

### 2. User Management
```groovy
// Disable user signup
jenkins.model.Jenkins.instance.setDisableSignup(true)

// Enable CAPTCHA for login
jenkins.security.SecurityRealm.enableCaptcha = true
```

### 3. Authorization Strategy
- Use "Matrix-based security" or "Project-based Matrix Authorization"
- Follow principle of least privilege
- Regularly audit user permissions
- Use groups instead of individual user permissions

### 4. API Token Security
```bash
# Use API tokens instead of passwords
# Rotate tokens regularly
# Limit token scope when possible
curl -u username:api-token http://jenkins.example.com/api/json
```

## System Security

### 1. Jenkins Updates
- Keep Jenkins core updated to latest LTS version
- Update plugins regularly
- Subscribe to Jenkins security advisories
- Test updates in staging environment first

### 2. Plugin Security
```groovy
// Disable unused plugins
jenkins.model.Jenkins.instance.pluginManager.plugins.each { plugin ->
    if (!plugin.isEnabled()) {
        println "Disabled plugin: ${plugin.shortName}"
    }
}
```

### 3. System Configuration
```bash
# Run Jenkins as non-root user
sudo adduser --system --shell /bin/bash --gecos 'Jenkins' --group --home /var/jenkins_home jenkins

# Set proper file permissions
chown -R jenkins:jenkins /var/jenkins_home
chmod -R 750 /var/jenkins_home
```

## Network Security

### 1. HTTPS Configuration
```bash
# Generate certificate
keytool -genkey -keyalg RSA -alias jenkins -keystore jenkins.jks

# Start Jenkins with HTTPS
java -jar jenkins.war --httpPort=-1 --httpsPort=8443 --httpsKeyStore=jenkins.jks
```

### 2. Firewall Configuration
```bash
# Only allow necessary ports
ufw allow 8080  # Jenkins web interface
ufw allow 22    # SSH
ufw deny 50000  # Block agent port from internet
```

### 3. Reverse Proxy Security
```nginx
# Nginx security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

## Build Security

### 1. Sandboxed Execution
```groovy
// Use Pipeline Global Libraries for trusted code
@Library('trusted-lib') _

pipeline {
    agent {
        docker {
            image 'maven:3.8-openjdk-11'
            // Run as non-root user
            args '--user 1000:1000'
        }
    }
}
```

### 2. Credential Management
```groovy
// Use Jenkins credentials store
withCredentials([usernamePassword(credentialsId: 'github-creds', 
                                  usernameVariable: 'USERNAME', 
                                  passwordVariable: 'PASSWORD')]) {
    sh 'git clone https://$USERNAME:$PASSWORD@github.com/company/repo.git'
}
```

### 3. Script Security
- Enable "Script Security Plugin"
- Review and approve all pipeline scripts
- Use shared libraries for common functions
- Implement script approval workflow

## Data Protection

### 1. Backup Security
```bash
# Encrypt backups
tar -czf - /var/jenkins_home | gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output jenkins-backup.tar.gz.gpg

# Secure backup storage
rsync -avz --delete /var/jenkins_home/ backup-server:/secure/jenkins-backup/
```

### 2. Log Security
```bash
# Rotate and secure logs
logrotate -f /etc/logrotate.d/jenkins

# Set log permissions
chmod 640 /var/log/jenkins/*.log
chown jenkins:adm /var/log/jenkins/*.log
```

### 3. Workspace Cleanup
```groovy
// Automatic workspace cleanup
pipeline {
    options {
        skipDefaultCheckout(true)
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    post {
        always {
            deleteDir()
        }
    }
}
```

## Monitoring and Auditing

### 1. Audit Logging
```groovy
// Enable audit trail plugin
def auditTrail = Jenkins.instance.getExtensionList(hudson.plugins.audit_trail.AuditTrailPlugin.class)[0]
auditTrail.configure()
```

### 2. Security Monitoring
```bash
# Monitor failed login attempts
grep "loginError" /var/log/jenkins/jenkins.log | tail -20

# Check for unusual activity
grep -E "(SEVERE|WARNING)" /var/log/jenkins/jenkins.log | tail -50
```

### 3. Regular Security Audits
- Review user accounts and permissions quarterly
- Audit installed plugins and their permissions
- Check for unused credentials and clean up
- Verify backup and restore procedures

## Environment Security

### 1. Container Security
```dockerfile
# Use minimal base images
FROM openjdk:11-jre-slim

# Create non-root user
RUN groupadd -r jenkins && useradd -r -g jenkins jenkins

# Set secure file permissions
COPY --chown=jenkins:jenkins app.jar /app/app.jar

USER jenkins
```

### 2. Agent Security
```groovy
// Secure agent configuration
node('secure-agent') {
    // Limit agent capabilities
    stage('Build') {
        timeout(time: 30, unit: 'MINUTES') {
            sh 'mvn clean install'
        }
    }
}
```

### 3. Secret Management
```groovy
// Use external secret management
withCredentials([string(credentialsId: 'vault-token', variable: 'VAULT_TOKEN')]) {
    script {
        def secrets = sh(
            script: "vault kv get -format=json secret/myapp",
            returnStdout: true
        ).trim()
        def secretData = readJSON text: secrets
        env.DB_PASSWORD = secretData.data.db_password
    }
}
```

## Compliance and Governance

### 1. Pipeline Governance
```groovy
// Enforce pipeline standards
@Library('company-standards') _

pipeline {
    agent any
    stages {
        stage('Compliance Check') {
            steps {
                script {
                    complianceCheck()  // From shared library
                    securityScan()     // From shared library
                }
            }
        }
    }
}
```

### 2. Configuration as Code
```yaml
# jenkins.yaml - Configuration as Code
jenkins:
  securityRealm:
    ldap:
      configurations:
        - server: "ldap://ldap.company.com:389"
          rootDN: "dc=company,dc=com"
          userSearchBase: "ou=people"
          userSearch: "uid={0}"
  authorizationStrategy:
    projectMatrix:
      permissions:
        - "Overall/Administer:admin-group"
        - "Overall/Read:authenticated"
```

## Incident Response

### 1. Security Incident Plan
```bash
#!/bin/bash
# Security incident response script
echo "Jenkins Security Incident Response"

# Disable Jenkins immediately if compromised
systemctl stop jenkins

# Backup current state for forensics
tar -czf jenkins-incident-$(date +%Y%m%d-%H%M%S).tar.gz /var/jenkins_home

# Check for unauthorized changes
find /var/jenkins_home -type f -mtime -1 -ls

# Review recent logins
grep "Successful login" /var/log/jenkins/jenkins.log | tail -50
```

### 2. Recovery Procedures
```bash
# Restore from secure backup
systemctl stop jenkins
rm -rf /var/jenkins_home/*
tar -xzf jenkins-clean-backup.tar.gz -C /var/jenkins_home
chown -R jenkins:jenkins /var/jenkins_home
systemctl start jenkins
```

## Security Checklist

### Daily
- [ ] Review Jenkins security notifications
- [ ] Check for failed login attempts
- [ ] Monitor system resource usage

### Weekly  
- [ ] Review user access and permissions
- [ ] Check for plugin updates with security fixes
- [ ] Verify backup integrity

### Monthly
- [ ] Audit user accounts and remove unused ones
- [ ] Review and rotate API tokens
- [ ] Update security documentation
- [ ] Test incident response procedures

### Quarterly
- [ ] Full security audit
- [ ] Penetration testing
- [ ] Review and update security policies
- [ ] Security training for Jenkins administrators

## Emergency Contacts

- **Security Team**: security@company.com
- **Jenkins Admin**: jenkins-admin@company.com  
- **Infrastructure Team**: infra@company.com
- **Legal/Compliance**: legal@company.com

Remember: Security is not a one-time setup but an ongoing process. Regular monitoring, updates, and audits are essential for maintaining a secure Jenkins environment.
"""
    
    @mcp.prompt("jenkins_performance_optimization")
    async def performance_optimization() -> str:
        """
        Provide Jenkins performance optimization best practices.
        
        Returns:
            Detailed performance optimization guide
        """
        return """# Jenkins Performance Optimization Best Practices

## System-Level Optimization

### JVM Configuration
```bash
# Recommended JVM settings for Jenkins
JAVA_OPTS="-Xms2g -Xmx8g
           -XX:+UseG1GC
           -XX:+UseStringDeduplication
           -XX:MaxGCPauseMillis=100
           -XX:+UnlockExperimentalVMOptions
           -XX:+UseCGroupMemoryLimitForHeap
           -server"

# Additional performance options
JENKINS_OPTS="--sessionTimeout=1440
              --sessionEviction=3600"
```

### Memory Management
```groovy
// Monitor memory usage
System.gc()
Runtime runtime = Runtime.getRuntime()
long maxMemory = runtime.maxMemory() / 1024 / 1024
long totalMemory = runtime.totalMemory() / 1024 / 1024
long freeMemory = runtime.freeMemory() / 1024 / 1024
println "Max: ${maxMemory}MB, Total: ${totalMemory}MB, Free: ${freeMemory}MB"
```

### Storage Optimization
```bash
# Use SSD for Jenkins home
mount /dev/nvme0n1 /var/jenkins_home

# Separate builds and workspaces to different disks
mkdir -p /fast-storage/{builds,workspaces}
ln -sf /fast-storage/builds /var/jenkins_home/jobs
ln -sf /fast-storage/workspaces /var/jenkins_home/workspace
```

## Build Performance

### Pipeline Optimization
```groovy
pipeline {
    agent none
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }
    
    stages {
        stage('Parallel Execution') {
            parallel {
                stage('Unit Tests') {
                    agent { label 'test-fast' }
                    steps {
                        checkout scm
                        sh 'mvn test -Dmaven.test.failure.ignore=true'
                    }
                }
                stage('Integration Tests') {
                    agent { label 'test-integration' }
                    steps {
                        checkout scm
                        sh 'mvn verify -Pintegration-tests'
                    }
                }
                stage('Security Scan') {
                    agent { label 'security' }
                    steps {
                        checkout scm
                        sh 'sonar-scanner'
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up workspaces
            node('master') {
                cleanWs()
            }
        }
    }
}
```

### Build Caching
```groovy
// Maven cache optimization
pipeline {
    agent any
    tools {
        maven '3.8.4'
    }
    stages {
        stage('Build with Cache') {
            steps {
                // Use Maven daemon for faster builds
                sh 'mvn compile -Dmaven.compiler.useIncrementalCompilation=true'
                
                // Cache dependencies
                cache(maxCacheSize: 250, caches: [
                    arbitraryFileCache(
                        path: '.m2/repository',
                        includes: '**/*',
                        fingerprinting: true
                    )
                ]) {
                    sh 'mvn install'
                }
            }
        }
    }
}
```

### Workspace Management
```groovy
// Efficient workspace handling
pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
    }
    stages {
        stage('Optimized Checkout') {
            steps {
                // Shallow clone for faster checkout
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [
                        [$class: 'CloneOption', shallow: true, depth: 1],
                        [$class: 'SubmoduleOption', disableSubmodules: true]
                    ],
                    userRemoteConfigs: [[url: env.GIT_URL]]
                ])
            }
        }
        stage('Incremental Build') {
            steps {
                // Only build changed modules
                sh '''
                CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
                if echo "$CHANGED_FILES" | grep -q "^frontend/"; then
                    echo "Building frontend"
                    cd frontend && npm run build
                fi
                if echo "$CHANGED_FILES" | grep -q "^backend/"; then
                    echo "Building backend"
                    cd backend && mvn compile
                fi
                '''
            }
        }
    }
}
```

## Node and Agent Optimization

### Node Distribution
```groovy
// Smart node allocation
pipeline {
    agent none
    stages {
        stage('CPU Intensive') {
            agent { label 'high-cpu' }
            steps {
                sh 'make compile -j$(nproc)'
            }
        }
        stage('Memory Intensive') {
            agent { label 'high-memory' }
            steps {
                sh 'java -Xmx4g -jar analysis.jar'
            }
        }
        stage('Fast I/O') {
            agent { label 'ssd-storage' }
            steps {
                sh 'npm install && npm run build'
            }
        }
    }
}
```

### Agent Configuration
```bash
# Optimize agent JVM
AGENT_OPTS="-Xms512m -Xmx2g
            -XX:+UseG1GC
            -Djava.awt.headless=true"

# Increase agent executors based on CPU cores
EXECUTORS=$(($(nproc) * 2))
```

## Plugin Performance

### Plugin Selection
```groovy
// Disable heavy plugins not in use
def jenkins = Jenkins.instance
def pluginManager = jenkins.pluginManager

// List of heavy plugins to consider disabling
def heavyPlugins = [
    'blueocean',
    'pipeline-stage-view',
    'build-pipeline-plugin'
]

heavyPlugins.each { pluginName ->
    def plugin = pluginManager.getPlugin(pluginName)
    if (plugin && plugin.isEnabled()) {
        println "Consider disabling heavy plugin: ${pluginName}"
    }
}
```

### Plugin Updates
```bash
# Update plugins via CLI for better performance
java -jar jenkins-cli.jar -s http://localhost:8080/ install-plugin plugin-name -restart
```

## Database Optimization

### H2 Database Tuning
```bash
# H2 database optimization
JENKINS_OPTS="$JENKINS_OPTS
              -Dh2.objectCache=256
              -Dh2.cacheSize=64000"
```

### External Database
```sql
-- PostgreSQL optimization for Jenkins
CREATE INDEX CONCURRENTLY idx_builds_job_number ON builds(job_name, build_number);
CREATE INDEX CONCURRENTLY idx_builds_timestamp ON builds(timestamp);
VACUUM ANALYZE builds;

-- Connection pool optimization
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

## Monitoring and Metrics

### Performance Monitoring
```groovy
// Custom performance metrics
pipeline {
    agent any
    stages {
        stage('Performance Tracking') {
            steps {
                script {
                    def startTime = System.currentTimeMillis()
                    
                    // Your build steps
                    sh 'mvn clean install'
                    
                    def duration = System.currentTimeMillis() - startTime
                    def buildNumber = env.BUILD_NUMBER
                    
                    // Log performance data
                    writeFile file: 'performance.log', 
                             text: "${buildNumber},${duration},${env.JOB_NAME}\n"
                    
                    // Send to monitoring system
                    sh '''
                    curl -X POST http://monitoring.company.com/metrics \\
                         -d "jenkins.build.duration=${duration}" \\
                         -d "job=${env.JOB_NAME}" \\
                         -d "build=${buildNumber}"
                    '''
                }
            }
        }
    }
}
```

### System Monitoring
```bash
#!/bin/bash
# Jenkins performance monitoring script

echo "=== Jenkins Performance Report ==="
echo "Timestamp: $(date)"

# CPU and Memory
echo -e "\n--- System Resources ---"
top -bn1 | grep -E "(Cpu|Mem|jenkins)"

# Disk I/O
echo -e "\n--- Disk Usage ---"
df -h | grep -E "(jenkins|home)"
iostat -x 1 1 | tail -n +4

# Network
echo -e "\n--- Network Connections ---"
netstat -an | grep :8080 | wc -l

# Jenkins-specific metrics
echo -e "\n--- Jenkins Metrics ---"
curl -s "http://localhost:8080/metrics/currentUser/api/json?tree=gauges[*[value]]" | \
jq '.gauges | to_entries[] | select(.key | contains("executor")) | {key: .key, value: .value.value}'
```

## Cleanup and Maintenance

### Automated Cleanup
```groovy
// Automated workspace cleanup
pipeline {
    agent any
    triggers {
        cron('H 2 * * *')  // Run daily at 2 AM
    }
    stages {
        stage('Cleanup') {
            steps {
                script {
                    // Clean old workspaces
                    def jenkins = Jenkins.instance
                    jenkins.getAllItems(Job.class).each { job ->
                        job.builds.each { build ->
                            if (build.timestamp.before(new Date() - 30)) {
                                build.delete()
                            }
                        }
                    }
                    
                    // Clean temporary files
                    sh '''
                    find /var/jenkins_home/workspace -type f -name "*.tmp" -mtime +1 -delete
                    find /var/jenkins_home/workspace -type d -empty -delete
                    '''
                }
            }
        }
    }
}
```

## Load Balancing and Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml for Jenkins cluster
version: '3.8'
services:
  jenkins-master:
    image: jenkins/jenkins:lts
    ports:
      - "8080:8080"
      - "50000:50000"
    environment:
      - JENKINS_OPTS=--sessionTimeout=1440
    
  jenkins-agent-1:
    image: jenkins/ssh-agent
    environment:
      - JENKINS_AGENT_SSH_PUBKEY=ssh-rsa AAAA...
    
  jenkins-agent-2:
    image: jenkins/ssh-agent
    environment:
      - JENKINS_AGENT_SSH_PUBKEY=ssh-rsa AAAA...
```

### Load Testing
```bash
# Apache Bench for Jenkins load testing
ab -n 1000 -c 10 -H "Authorization: Basic $(echo -n user:password | base64)" \
   http://localhost:8080/api/json

# JMeter test plan for Jenkins
jmeter -n -t jenkins-load-test.jmx -l results.jtl
```

## Performance Tuning Checklist

### System Level
- [ ] Optimize JVM settings for your workload
- [ ] Use SSD storage for Jenkins home
- [ ] Configure adequate RAM (minimum 4GB, recommended 8GB+)
- [ ] Set up proper swap space
- [ ] Optimize network configuration

### Jenkins Configuration
- [ ] Configure appropriate number of executors
- [ ] Enable build discarder policies
- [ ] Optimize plugin selection
- [ ] Use pipeline as code
- [ ] Implement proper caching strategies

### Build Optimization
- [ ] Parallelize build stages
- [ ] Use incremental builds
- [ ] Optimize dependency management
- [ ] Implement proper workspace cleanup
- [ ] Use appropriate build tools and versions

### Monitoring
- [ ] Set up performance monitoring
- [ ] Configure alerting for performance issues
- [ ] Regular performance audits
- [ ] Capacity planning based on growth

Remember: Performance optimization is an iterative process. Make incremental changes and measure their impact before implementing additional optimizations.
"""