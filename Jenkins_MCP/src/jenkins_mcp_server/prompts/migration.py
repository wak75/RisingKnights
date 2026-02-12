"""Jenkins migration and upgrade prompts."""


def register_prompts(mcp):
    """Register migration and upgrade prompts with the MCP server."""
    
    @mcp.prompt("jenkins_migration_guide")
    async def migration_guide() -> str:
        """
        Provide comprehensive Jenkins migration guide.
        
        Returns:
            Detailed migration guide for Jenkins
        """
        return """# Jenkins Migration Guide

## Pre-Migration Planning

### Assessment Phase
```bash
#!/bin/bash
# Jenkins migration assessment script

echo "=== Jenkins Migration Assessment ==="

# Check current Jenkins version
JENKINS_VERSION=$(curl -s http://localhost:8080/api/json | jq -r '.version')
echo "Current Jenkins Version: $JENKINS_VERSION"

# Check installed plugins
curl -s http://localhost:8080/pluginManager/api/json?depth=1 | jq '.plugins[] | {shortName, version, hasUpdate}'

# Check job count and types
echo "Job Statistics:"
curl -s http://localhost:8080/api/json | jq '.jobs | length'

# Check node information
echo "Node Information:"
curl -s http://localhost:8080/computer/api/json | jq '.computer[] | {displayName, offline, numExecutors}'

# Check disk usage
echo "Disk Usage:"
du -sh $JENKINS_HOME
```

### Migration Checklist
- [ ] Document current Jenkins version and configuration
- [ ] Inventory all installed plugins
- [ ] List all jobs and their configurations
- [ ] Document user accounts and permissions
- [ ] Identify custom scripts and tools
- [ ] Map integrations with external systems
- [ ] Document backup and recovery procedures
- [ ] Plan downtime window
- [ ] Prepare rollback plan

### Environment Preparation
```yaml
# docker-compose.yml for testing environment
version: '3.8'
services:
  jenkins-old:
    image: jenkins/jenkins:2.401.3-lts
    ports:
      - "8080:8080"
    volumes:
      - jenkins_old_home:/var/jenkins_home
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
  
  jenkins-new:
    image: jenkins/jenkins:2.426.1-lts
    ports:
      - "8081:8080"
    volumes:
      - jenkins_new_home:/var/jenkins_home
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false

volumes:
  jenkins_old_home:
  jenkins_new_home:
```

## Migration Strategies

### 1. Blue-Green Migration
```bash
#!/bin/bash
# Blue-Green Jenkins migration script

# Phase 1: Setup new Jenkins (Green)
echo "Setting up new Jenkins instance..."
docker-compose up -d jenkins-new

# Phase 2: Data migration
echo "Migrating Jenkins data..."
docker exec jenkins-old tar -czf /tmp/jenkins-backup.tar.gz -C /var/jenkins_home .
docker cp jenkins-old:/tmp/jenkins-backup.tar.gz ./jenkins-backup.tar.gz
docker cp ./jenkins-backup.tar.gz jenkins-new:/tmp/jenkins-backup.tar.gz
docker exec jenkins-new tar -xzf /tmp/jenkins-backup.tar.gz -C /var/jenkins_home

# Phase 3: Verification
echo "Verifying migration..."
./verify-migration.sh

# Phase 4: Switch traffic
echo "Switching traffic to new instance..."
# Update load balancer configuration
# Update DNS records
# Verify all systems are working

# Phase 5: Cleanup old instance
echo "Migration completed. Ready to cleanup old instance."
```

### 2. Rolling Migration
```groovy
// Groovy script for rolling migration
pipeline {
    agent any
    
    stages {
        stage('Migration Preparation') {
            steps {
                script {
                    // Stop accepting new builds
                    Jenkins.instance.doQuietDown()
                    
                    // Wait for running builds to complete
                    while (Jenkins.instance.queue.items.length > 0 || 
                           Jenkins.instance.computers.any { it.countBusy() > 0 }) {
                        echo "Waiting for builds to complete..."
                        sleep(30)
                    }
                }
            }
        }
        
        stage('Data Export') {
            steps {
                sh '''
                    mkdir -p migration-data
                    
                    # Export job configurations
                    java -jar jenkins-cli.jar -s http://localhost:8080 list-jobs | while read job; do
                        java -jar jenkins-cli.jar -s http://localhost:8080 get-job "$job" > "migration-data/${job}.xml"
                    done
                    
                    # Export global configuration
                    cp $JENKINS_HOME/config.xml migration-data/
                    cp -r $JENKINS_HOME/users migration-data/
                    cp -r $JENKINS_HOME/plugins migration-data/
                '''
            }
        }
        
        stage('New Instance Setup') {
            steps {
                sh '''
                    # Start new Jenkins instance
                    docker run -d --name jenkins-new \
                        -p 8081:8080 \
                        -v jenkins_new_home:/var/jenkins_home \
                        jenkins/jenkins:lts
                    
                    # Wait for Jenkins to start
                    while ! curl -s http://localhost:8081/api/json; do
                        sleep 10
                    done
                '''
            }
        }
        
        stage('Data Import') {
            steps {
                sh '''
                    # Import job configurations
                    for job_file in migration-data/*.xml; do
                        job_name=$(basename "$job_file" .xml)
                        java -jar jenkins-cli.jar -s http://localhost:8081 create-job "$job_name" < "$job_file"
                    done
                    
                    # Import users and permissions
                    docker cp migration-data/users jenkins-new:/var/jenkins_home/
                    docker restart jenkins-new
                '''
            }
        }
    }
}
```

### 3. Configuration as Code Migration
```yaml
# jenkins.yaml - Configuration as Code
jenkins:
  systemMessage: "Migrated Jenkins Instance"
  numExecutors: 4
  mode: NORMAL
  
  securityRealm:
    ldap:
      configurations:
        - server: "ldap://ldap.company.com:389"
          rootDN: "dc=company,dc=com"
          userSearchBase: "ou=users"
          userSearch: "uid={0}"
          groupSearchBase: "ou=groups"
          
  authorizationStrategy:
    projectMatrix:
      permissions:
        - "Overall/Administer:admin-group"
        - "Job/Build:developer-group"
        - "Job/Read:all-users"

  nodes:
    - permanent:
        name: "build-node-1"
        remoteFS: "/home/jenkins"
        launcher:
          ssh:
            host: "build01.company.com"
            credentialsId: "ssh-key"
        retentionStrategy: "always"

jobs:
  - script: |
      folder('migration-jobs') {
        description('Jobs migrated from old Jenkins')
      }
      
      pipelineJob('migration-jobs/sample-pipeline') {
        definition {
          cpsScm {
            scm {
              git {
                remote {
                  url('https://github.com/company/sample-app.git')
                }
                branch('main')
              }
            }
            scriptPath('Jenkinsfile')
          }
        }
      }

credentials:
  system:
    domainCredentials:
      - credentials:
          - usernamePassword:
              scope: GLOBAL
              id: "git-credentials"
              username: "jenkins-user"
              password: "${GIT_PASSWORD}"
              description: "Git repository credentials"
```

## Plugin Migration

### Plugin Compatibility Check
```bash
#!/bin/bash
# Plugin compatibility checker

OLD_JENKINS_VERSION="2.401.3"
NEW_JENKINS_VERSION="2.426.1"

echo "Checking plugin compatibility..."

# Get list of installed plugins
curl -s http://localhost:8080/pluginManager/api/json?depth=2 | jq -r '.plugins[] | "\(.shortName):\(.version)"' > current-plugins.txt

# Check each plugin compatibility
while IFS=: read -r plugin version; do
    echo "Checking $plugin:$version"
    
    # Query Jenkins plugin site for compatibility
    compatibility=$(curl -s "https://plugins.jenkins.io/api/plugin/$plugin" | jq -r ".version.releases[] | select(.version == \"$version\") | .compatibleSinceVersion")
    
    if [[ "$compatibility" > "$NEW_JENKINS_VERSION" ]]; then
        echo "WARNING: $plugin:$version may not be compatible with Jenkins $NEW_JENKINS_VERSION"
        echo "  Compatible since: $compatibility"
    else
        echo "OK: $plugin:$version is compatible"
    fi
done < current-plugins.txt
```

### Plugin Migration Script
```groovy
// Plugin migration script
@Grab('org.jenkins-ci:version-number:1.8')
import hudson.PluginManager
import jenkins.model.Jenkins
import org.apache.commons.io.FileUtils

def migratePlugins() {
    def jenkins = Jenkins.instance
    def pluginManager = jenkins.pluginManager
    
    // Export plugin list
    def plugins = []
    pluginManager.plugins.each { plugin ->
        plugins << [
            shortName: plugin.shortName,
            version: plugin.version,
            enabled: plugin.enabled,
            pinned: plugin.pinned
        ]
    }
    
    // Save to file
    def pluginJson = new groovy.json.JsonBuilder(plugins)
    new File(jenkins.rootDir, 'migrated-plugins.json').text = pluginJson.toPrettyString()
    
    // Generate installation script
    def installScript = new StringBuilder()
    installScript.append("#!/bin/bash\n")
    installScript.append("# Plugin installation script for new Jenkins instance\n\n")
    
    plugins.each { plugin ->
        installScript.append("java -jar jenkins-cli.jar -s http://localhost:8080 install-plugin ${plugin.shortName}:${plugin.version}\n")
    }
    
    new File(jenkins.rootDir, 'install-plugins.sh').text = installScript.toString()
    
    println "Plugin migration data exported to:"
    println "- migrated-plugins.json"
    println "- install-plugins.sh"
}

migratePlugins()
```

## Job Migration

### Job Export/Import Scripts
```bash
#!/bin/bash
# Job migration script

JENKINS_URL="http://localhost:8080"
JENKINS_CLI="java -jar jenkins-cli.jar -s $JENKINS_URL"

# Function to export all jobs
export_jobs() {
    echo "Exporting jobs..."
    mkdir -p job-configs
    
    # Get list of all jobs
    $JENKINS_CLI list-jobs | while read job; do
        echo "Exporting job: $job"
        $JENKINS_CLI get-job "$job" > "job-configs/${job}.xml"
    done
    
    # Export views
    $JENKINS_CLI list-views | while read view; do
        echo "Exporting view: $view"
        $JENKINS_CLI get-view "$view" > "job-configs/view-${view}.xml"
    done
}

# Function to import jobs to new Jenkins
import_jobs() {
    NEW_JENKINS_URL="http://localhost:8081"
    NEW_JENKINS_CLI="java -jar jenkins-cli.jar -s $NEW_JENKINS_URL"
    
    echo "Importing jobs..."
    
    # Import jobs
    for job_file in job-configs/*.xml; do
        if [[ $(basename "$job_file") != view-* ]]; then
            job_name=$(basename "$job_file" .xml)
            echo "Importing job: $job_name"
            $NEW_JENKINS_CLI create-job "$job_name" < "$job_file"
        fi
    done
    
    # Import views
    for view_file in job-configs/view-*.xml; do
        view_name=$(basename "$view_file" .xml | sed 's/view-//')
        echo "Importing view: $view_name"
        $NEW_JENKINS_CLI create-view "$view_name" < "$view_file"
    done
}

# Execute export and import
export_jobs
import_jobs
```

### Pipeline Migration
```groovy
// Pipeline job migration script
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition

def migratePipelines() {
    def jenkins = Jenkins.instance
    def migrationReport = []
    
    jenkins.allItems(WorkflowJob.class).each { job ->
        try {
            def jobData = [
                name: job.name,
                fullName: job.fullName,
                description: job.description,
                disabled: job.disabled,
                definition: null,
                triggers: [],
                properties: []
            ]
            
            // Get pipeline definition
            if (job.definition instanceof CpsFlowDefinition) {
                jobData.definition = [
                    type: 'pipeline',
                    script: job.definition.script,
                    sandbox: job.definition.sandbox
                ]
            }
            
            // Get triggers
            job.triggers.each { trigger ->
                jobData.triggers << [
                    type: trigger.class.simpleName,
                    spec: trigger.spec
                ]
            }
            
            // Get job properties
            job.jobProperties.each { property ->
                jobData.properties << [
                    type: property.class.simpleName,
                    data: property.toString()
                ]
            }
            
            migrationReport << jobData
            
        } catch (Exception e) {
            println "Error migrating job ${job.name}: ${e.message}"
        }
    }
    
    // Save migration report
    def reportJson = new groovy.json.JsonBuilder(migrationReport)
    new File(jenkins.rootDir, 'pipeline-migration-report.json').text = reportJson.toPrettyString()
    
    println "Pipeline migration report saved to pipeline-migration-report.json"
}

migratePipelines()
```

## Data Migration

### Complete Backup Script
```bash
#!/bin/bash
# Complete Jenkins backup script

JENKINS_HOME="/var/jenkins_home"
BACKUP_DIR="/backup/jenkins-$(date +%Y%m%d_%H%M%S)"
JENKINS_URL="http://localhost:8080"

echo "Starting Jenkins backup to $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Stop Jenkins to ensure consistent backup
echo "Stopping Jenkins..."
systemctl stop jenkins

# Backup Jenkins home directory
echo "Backing up Jenkins home..."
tar -czf "$BACKUP_DIR/jenkins-home.tar.gz" -C "$JENKINS_HOME" .

# Backup database if using external database
if [ -f "$JENKINS_HOME/database.xml" ]; then
    echo "Backing up database..."
    # Add database backup commands here
fi

# Create inventory of current state
echo "Creating inventory..."
cat > "$BACKUP_DIR/inventory.txt" << EOF
Backup Date: $(date)
Jenkins Version: $(cat $JENKINS_HOME/jenkins.install.UpgradeWizard.state 2>/dev/null || echo "Unknown")
Java Version: $(java -version 2>&1 | head -n 1)
OS Information: $(uname -a)
Disk Usage: $(du -sh $JENKINS_HOME)
Plugin Count: $(find $JENKINS_HOME/plugins -name "*.hpi" | wc -l)
Job Count: $(find $JENKINS_HOME/jobs -maxdepth 1 -type d | wc -l)
User Count: $(find $JENKINS_HOME/users -maxdepth 1 -type d | wc -l)
EOF

# Start Jenkins again
echo "Starting Jenkins..."
systemctl start jenkins

echo "Backup completed: $BACKUP_DIR"
```

### Restore Script
```bash
#!/bin/bash
# Jenkins restore script

BACKUP_FILE="$1"
JENKINS_HOME="/var/jenkins_home"
JENKINS_URL="http://localhost:8080"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file.tar.gz>"
    exit 1
fi

echo "Restoring Jenkins from $BACKUP_FILE"

# Stop Jenkins
echo "Stopping Jenkins..."
systemctl stop jenkins

# Backup current state (just in case)
echo "Creating safety backup..."
tar -czf "/tmp/jenkins-pre-restore-$(date +%Y%m%d_%H%M%S).tar.gz" -C "$JENKINS_HOME" .

# Clear current Jenkins home
echo "Clearing current Jenkins home..."
rm -rf "$JENKINS_HOME"/*

# Restore from backup
echo "Restoring from backup..."
tar -xzf "$BACKUP_FILE" -C "$JENKINS_HOME"

# Fix permissions
echo "Fixing permissions..."
chown -R jenkins:jenkins "$JENKINS_HOME"

# Start Jenkins
echo "Starting Jenkins..."
systemctl start jenkins

# Wait for Jenkins to start
echo "Waiting for Jenkins to start..."
while ! curl -s "$JENKINS_URL/api/json" > /dev/null; do
    sleep 5
done

echo "Jenkins restore completed successfully"
```

## Version Upgrade Guide

### Incremental Upgrade Strategy
```bash
#!/bin/bash
# Incremental Jenkins upgrade script

CURRENT_VERSION="2.401.3"
TARGET_VERSION="2.426.1"
JENKINS_HOME="/var/jenkins_home"

# Define upgrade path
UPGRADE_PATH=(
    "2.401.3"
    "2.414.1"
    "2.426.1"
)

upgrade_jenkins() {
    local from_version=$1
    local to_version=$2
    
    echo "Upgrading from $from_version to $to_version"
    
    # Create backup before upgrade
    backup_jenkins "$from_version"
    
    # Download new Jenkins WAR
    wget "https://get.jenkins.io/war-stable/$to_version/jenkins.war" -O "/tmp/jenkins-$to_version.war"
    
    # Stop Jenkins
    systemctl stop jenkins
    
    # Replace Jenkins WAR
    cp "/tmp/jenkins-$to_version.war" "/usr/share/jenkins/jenkins.war"
    
    # Start Jenkins
    systemctl start jenkins
    
    # Wait for startup and verify
    wait_for_jenkins
    verify_upgrade "$to_version"
}

wait_for_jenkins() {
    echo "Waiting for Jenkins to start..."
    while ! curl -s http://localhost:8080/api/json > /dev/null; do
        sleep 10
    done
    echo "Jenkins is running"
}

verify_upgrade() {
    local expected_version=$1
    local actual_version=$(curl -s http://localhost:8080/api/json | jq -r '.version')
    
    if [ "$actual_version" = "$expected_version" ]; then
        echo "Upgrade to $expected_version successful"
    else
        echo "Upgrade failed. Expected: $expected_version, Actual: $actual_version"
        exit 1
    fi
}

backup_jenkins() {
    local version=$1
    local backup_dir="/backup/pre-upgrade-$version-$(date +%Y%m%d_%H%M%S)"
    
    echo "Creating backup before upgrade to $backup_dir"
    mkdir -p "$backup_dir"
    tar -czf "$backup_dir/jenkins-home.tar.gz" -C "$JENKINS_HOME" .
}

# Execute incremental upgrades
for i in "${!UPGRADE_PATH[@]}"; do
    if [ $i -gt 0 ]; then
        upgrade_jenkins "${UPGRADE_PATH[$((i-1))]}" "${UPGRADE_PATH[$i]}"
    fi
done

echo "All upgrades completed successfully"
```

## Migration Validation

### Validation Script
```bash
#!/bin/bash
# Jenkins migration validation script

OLD_JENKINS="http://localhost:8080"
NEW_JENKINS="http://localhost:8081"

echo "=== Jenkins Migration Validation ==="

# Compare job counts
echo "Comparing job counts..."
OLD_JOB_COUNT=$(curl -s $OLD_JENKINS/api/json | jq '.jobs | length')
NEW_JOB_COUNT=$(curl -s $NEW_JENKINS/api/json | jq '.jobs | length')

echo "Old Jenkins: $OLD_JOB_COUNT jobs"
echo "New Jenkins: $NEW_JOB_COUNT jobs"

if [ "$OLD_JOB_COUNT" -eq "$NEW_JOB_COUNT" ]; then
    echo "✓ Job count matches"
else
    echo "✗ Job count mismatch"
fi

# Compare plugin counts
echo "Comparing plugin counts..."
OLD_PLUGIN_COUNT=$(curl -s $OLD_JENKINS/pluginManager/api/json | jq '.plugins | length')
NEW_PLUGIN_COUNT=$(curl -s $NEW_JENKINS/pluginManager/api/json | jq '.plugins | length')

echo "Old Jenkins: $OLD_PLUGIN_COUNT plugins"
echo "New Jenkins: $NEW_PLUGIN_COUNT plugins"

# Compare user counts
echo "Comparing user counts..."
OLD_USER_COUNT=$(curl -s $OLD_JENKINS/asynchPeople/api/json | jq '.users | length')
NEW_USER_COUNT=$(curl -s $NEW_JENKINS/asynchPeople/api/json | jq '.users | length')

echo "Old Jenkins: $OLD_USER_COUNT users"
echo "New Jenkins: $NEW_USER_COUNT users"

# Test job execution
echo "Testing job execution..."
curl -X POST $NEW_JENKINS/job/test-job/build

# Generate validation report
cat > migration-validation-report.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Jenkins Migration Validation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .success { color: green; }
        .error { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Jenkins Migration Validation Report</h1>
    <p>Migration Date: $(date)</p>
    
    <h2>Summary</h2>
    <table>
        <tr><th>Component</th><th>Old Jenkins</th><th>New Jenkins</th><th>Status</th></tr>
        <tr><td>Jobs</td><td>$OLD_JOB_COUNT</td><td>$NEW_JOB_COUNT</td><td class="success">✓</td></tr>
        <tr><td>Plugins</td><td>$OLD_PLUGIN_COUNT</td><td>$NEW_PLUGIN_COUNT</td><td class="success">✓</td></tr>
        <tr><td>Users</td><td>$OLD_USER_COUNT</td><td>$NEW_USER_COUNT</td><td class="success">✓</td></tr>
    </table>
    
    <h2>Recommendations</h2>
    <ul>
        <li>Monitor system performance for 24-48 hours</li>
        <li>Test critical pipelines</li>
        <li>Verify all integrations are working</li>
        <li>Update documentation and runbooks</li>
        <li>Schedule cleanup of old Jenkins instance</li>
    </ul>
</body>
</html>
EOF

echo "Validation report generated: migration-validation-report.html"
```

## Post-Migration Tasks

### Cleanup Script
```bash
#!/bin/bash
# Post-migration cleanup script

echo "=== Post-Migration Cleanup ==="

# Update monitoring systems
echo "Updating monitoring configurations..."
# Update monitoring URLs, alerting rules, etc.

# Update documentation
echo "Documentation updates required:"
echo "- Update Jenkins URL in documentation"
echo "- Update integration configurations"
echo "- Update backup procedures"
echo "- Update disaster recovery plans"

# Update integrations
echo "Integration updates required:"
echo "- Update webhook URLs in repositories"
echo "- Update CI/CD pipeline configurations"
echo "- Update deployment scripts"
echo "- Update monitoring dashboards"

# Performance optimization
echo "Optimizing new Jenkins instance..."
# Configure JVM settings
# Optimize plugin configurations
# Set up log rotation
# Configure backup schedules

# Security hardening
echo "Applying security hardening..."
# Update security configurations
# Review user permissions
# Update SSL certificates
# Configure firewall rules

echo "Post-migration cleanup completed"
```

## Rollback Procedures

### Emergency Rollback Script
```bash
#!/bin/bash
# Emergency rollback script

BACKUP_FILE="$1"
JENKINS_HOME="/var/jenkins_home"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file.tar.gz>"
    exit 1
fi

echo "EMERGENCY ROLLBACK - Restoring Jenkins from $BACKUP_FILE"

# Stop current Jenkins
systemctl stop jenkins

# Restore from pre-migration backup
tar -xzf "$BACKUP_FILE" -C "$JENKINS_HOME"

# Fix permissions
chown -R jenkins:jenkins "$JENKINS_HOME"

# Start Jenkins
systemctl start jenkins

echo "Emergency rollback completed"
```

## Migration Best Practices

### Key Recommendations
1. **Always test migrations in staging first**
2. **Plan for sufficient downtime**
3. **Have multiple backup strategies**
4. **Document every step of the process**
5. **Prepare detailed rollback plans**
6. **Validate all functionality post-migration**
7. **Monitor performance after migration**
8. **Update all documentation and integrations**

### Common Pitfalls to Avoid
- Insufficient testing in staging environment
- Not backing up plugin configurations
- Forgetting to update integrations
- Not planning for plugin compatibility issues
- Insufficient downtime planning
- Not validating user permissions
- Forgetting to update monitoring systems
- Not communicating changes to stakeholders

Remember: A successful Jenkins migration requires careful planning, thorough testing, and detailed documentation. Always have a rollback plan ready!
"""
    
    @mcp.prompt("jenkins_upgrade_checklist")
    async def upgrade_checklist() -> str:
        """
        Provide Jenkins upgrade checklist and procedures.
        
        Returns:
            Detailed upgrade checklist for Jenkins
        """
        return """# Jenkins Upgrade Checklist

## Pre-Upgrade Planning

### Environment Assessment
- [ ] Document current Jenkins version
- [ ] List all installed plugins and versions
- [ ] Document JVM settings and system properties
- [ ] Record system specifications (CPU, RAM, disk)
- [ ] Document integrations and dependencies
- [ ] List customizations and modifications
- [ ] Review change log for target version

### Compatibility Check
```bash
#!/bin/bash
# Jenkins compatibility check script

CURRENT_VERSION=$(curl -s http://localhost:8080/api/json | jq -r '.version')
TARGET_VERSION="2.426.1"  # Replace with target version

echo "Current Version: $CURRENT_VERSION"
echo "Target Version: $TARGET_VERSION"

# Check Java compatibility
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
echo "Java Version: $JAVA_VERSION"

# Check plugin compatibility
echo "Checking plugin compatibility..."
curl -s http://localhost:8080/pluginManager/api/json?depth=2 | \
  jq -r '.plugins[] | select(.hasUpdate == true) | "\(.shortName): \(.version) -> \(.latestVersion)"'
```

### Backup Strategy
- [ ] Full Jenkins home backup
- [ ] Database backup (if using external DB)
- [ ] Configuration export
- [ ] Plugin list export
- [ ] Job configuration backup
- [ ] User and permission backup
- [ ] Custom scripts and tools backup

### Testing Environment
- [ ] Set up staging environment
- [ ] Replicate production configuration
- [ ] Test upgrade process in staging
- [ ] Validate all functionality
- [ ] Test rollback procedures
- [ ] Document any issues found

## Upgrade Process

### Step 1: Pre-Upgrade Backup
```bash
#!/bin/bash
# Pre-upgrade backup script

JENKINS_HOME="/var/jenkins_home"
BACKUP_DIR="/backup/pre-upgrade-$(date +%Y%m%d_%H%M%S)"
JENKINS_URL="http://localhost:8080"

echo "Creating pre-upgrade backup..."
mkdir -p "$BACKUP_DIR"

# Stop Jenkins for consistent backup
sudo systemctl stop jenkins

# Backup Jenkins home
tar -czf "$BACKUP_DIR/jenkins-home.tar.gz" -C "$JENKINS_HOME" .

# Export job configurations
mkdir -p "$BACKUP_DIR/jobs"
sudo systemctl start jenkins

# Wait for Jenkins to start
while ! curl -s $JENKINS_URL/api/json > /dev/null; do sleep 5; done

# Export all jobs
java -jar jenkins-cli.jar -s $JENKINS_URL list-jobs | while read job; do
    java -jar jenkins-cli.jar -s $JENKINS_URL get-job "$job" > "$BACKUP_DIR/jobs/${job}.xml"
done

# Export installed plugins
curl -s $JENKINS_URL/pluginManager/api/json?depth=1 | \
  jq -r '.plugins[] | "\(.shortName):\(.version)"' > "$BACKUP_DIR/plugins.txt"

# Export users
curl -s $JENKINS_URL/asynchPeople/api/json | \
  jq '.users' > "$BACKUP_DIR/users.json"

echo "Backup completed: $BACKUP_DIR"
```

### Step 2: Plugin Updates
```bash
#!/bin/bash
# Plugin update script

JENKINS_URL="http://localhost:8080"
JENKINS_CLI="java -jar jenkins-cli.jar -s $JENKINS_URL"

echo "Updating plugins..."

# Get list of plugins with updates
$JENKINS_CLI list-plugins | grep ")$" | awk '{print $1}' > plugins-to-update.txt

# Update plugins
while read plugin; do
    echo "Updating plugin: $plugin"
    $JENKINS_CLI install-plugin $plugin
done < plugins-to-update.txt

# Restart Jenkins to load updated plugins
echo "Restarting Jenkins..."
$JENKINS_CLI safe-restart

# Wait for restart
while ! curl -s $JENKINS_URL/api/json > /dev/null; do sleep 10; done
echo "Jenkins restarted successfully"
```

### Step 3: Jenkins Core Upgrade
```bash
#!/bin/bash
# Jenkins core upgrade script

CURRENT_VERSION=$(curl -s http://localhost:8080/api/json | jq -r '.version')
TARGET_VERSION="2.426.1"
JENKINS_HOME="/var/jenkins_home"
JENKINS_WAR="/usr/share/jenkins/jenkins.war"

echo "Upgrading Jenkins from $CURRENT_VERSION to $TARGET_VERSION"

# Download new Jenkins WAR
echo "Downloading Jenkins $TARGET_VERSION..."
wget "https://get.jenkins.io/war-stable/$TARGET_VERSION/jenkins.war" -O "/tmp/jenkins-$TARGET_VERSION.war"

# Verify download
if [ ! -f "/tmp/jenkins-$TARGET_VERSION.war" ]; then
    echo "Failed to download Jenkins WAR file"
    exit 1
fi

# Stop Jenkins
echo "Stopping Jenkins..."
sudo systemctl stop jenkins

# Backup current WAR file
cp "$JENKINS_WAR" "$JENKINS_WAR.backup"

# Install new WAR file
cp "/tmp/jenkins-$TARGET_VERSION.war" "$JENKINS_WAR"

# Start Jenkins
echo "Starting Jenkins with new version..."
sudo systemctl start jenkins

# Monitor startup
echo "Waiting for Jenkins to start..."
while ! curl -s http://localhost:8080/api/json > /dev/null; do
    sleep 10
    echo "Still waiting for Jenkins..."
done

# Verify upgrade
NEW_VERSION=$(curl -s http://localhost:8080/api/json | jq -r '.version')
echo "Upgrade completed. New version: $NEW_VERSION"

if [ "$NEW_VERSION" = "$TARGET_VERSION" ]; then
    echo "✓ Upgrade successful"
else
    echo "✗ Upgrade failed. Rolling back..."
    sudo systemctl stop jenkins
    cp "$JENKINS_WAR.backup" "$JENKINS_WAR"
    sudo systemctl start jenkins
    exit 1
fi
```

### Step 4: Post-Upgrade Validation
```bash
#!/bin/bash
# Post-upgrade validation script

JENKINS_URL="http://localhost:8080"

echo "=== Post-Upgrade Validation ==="

# Check Jenkins version
NEW_VERSION=$(curl -s $JENKINS_URL/api/json | jq -r '.version')
echo "Jenkins Version: $NEW_VERSION"

# Check system health
echo "System Health Check:"
curl -s $JENKINS_URL/manage/systemInfo | grep -E "(Available memory|Free disk space)"

# Check plugin status
echo "Plugin Status:"
FAILED_PLUGINS=$(curl -s $JENKINS_URL/pluginManager/api/json | jq -r '.plugins[] | select(.enabled == false) | .shortName')
if [ -z "$FAILED_PLUGINS" ]; then
    echo "✓ All plugins loaded successfully"
else
    echo "✗ Failed plugins: $FAILED_PLUGINS"
fi

# Test job execution
echo "Testing job execution..."
# Create a test job if it doesn't exist
TEST_JOB_CONFIG='<?xml version="1.0" encoding="UTF-8"?>
<project>
  <actions/>
  <description>Upgrade validation test job</description>
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
      <command>echo "Upgrade validation test successful"</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>'

echo "$TEST_JOB_CONFIG" | java -jar jenkins-cli.jar -s $JENKINS_URL create-job upgrade-test-job
java -jar jenkins-cli.jar -s $JENKINS_URL build upgrade-test-job

# Wait for build to complete
sleep 30

# Check build result
BUILD_RESULT=$(curl -s $JENKINS_URL/job/upgrade-test-job/lastBuild/api/json | jq -r '.result')
if [ "$BUILD_RESULT" = "SUCCESS" ]; then
    echo "✓ Test job executed successfully"
else
    echo "✗ Test job failed: $BUILD_RESULT"
fi

# Cleanup test job
java -jar jenkins-cli.jar -s $JENKINS_URL delete-job upgrade-test-job

echo "Validation completed"
```

## Rollback Procedures

### Emergency Rollback Checklist
- [ ] Stop current Jenkins instance
- [ ] Restore from pre-upgrade backup
- [ ] Verify rollback success
- [ ] Test critical functionality
- [ ] Update monitoring systems
- [ ] Notify stakeholders
- [ ] Document rollback reason

### Rollback Script
```bash
#!/bin/bash
# Emergency rollback script

BACKUP_DIR="$1"
JENKINS_HOME="/var/jenkins_home"
JENKINS_WAR="/usr/share/jenkins/jenkins.war"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup-directory>"
    exit 1
fi

echo "EMERGENCY ROLLBACK - Restoring from $BACKUP_DIR"

# Stop Jenkins
sudo systemctl stop jenkins

# Restore Jenkins home
echo "Restoring Jenkins home..."
rm -rf "$JENKINS_HOME"/*
tar -xzf "$BACKUP_DIR/jenkins-home.tar.gz" -C "$JENKINS_HOME"

# Restore WAR file if backed up
if [ -f "$JENKINS_WAR.backup" ]; then
    echo "Restoring Jenkins WAR file..."
    cp "$JENKINS_WAR.backup" "$JENKINS_WAR"
fi

# Fix permissions
chown -R jenkins:jenkins "$JENKINS_HOME"

# Start Jenkins
echo "Starting Jenkins..."
sudo systemctl start jenkins

# Wait for startup
while ! curl -s http://localhost:8080/api/json > /dev/null; do
    sleep 10
    echo "Waiting for Jenkins to start..."
done

# Verify rollback
CURRENT_VERSION=$(curl -s http://localhost:8080/api/json | jq -r '.version')
echo "Rollback completed. Current version: $CURRENT_VERSION"
```

## Upgrade Scenarios

### LTS to LTS Upgrade
```bash
#!/bin/bash
# LTS to LTS upgrade

# Example: 2.401.3 LTS to 2.414.1 LTS
OLD_LTS="2.401.3"
NEW_LTS="2.414.1"

echo "Upgrading from LTS $OLD_LTS to LTS $NEW_LTS"

# 1. Update all plugins first
echo "Step 1: Updating plugins..."
./update-plugins.sh

# 2. Backup current state
echo "Step 2: Creating backup..."
./backup-jenkins.sh

# 3. Upgrade Jenkins core
echo "Step 3: Upgrading Jenkins core..."
./upgrade-jenkins-core.sh $NEW_LTS

# 4. Validate upgrade
echo "Step 4: Validating upgrade..."
./validate-upgrade.sh

echo "LTS upgrade completed"
```

### Weekly to LTS Upgrade
```bash
#!/bin/bash
# Weekly release to LTS upgrade

CURRENT_WEEKLY="2.425"
TARGET_LTS="2.414.1"

echo "Upgrading from weekly $CURRENT_WEEKLY to LTS $TARGET_LTS"

# Note: This might be a downgrade in version number
# but upgrade in stability

# 1. Check for breaking changes
echo "Checking for breaking changes..."
curl -s "https://www.jenkins.io/changelog-stable/" | grep -A 20 "$TARGET_LTS"

# 2. Test in staging first
echo "Testing downgrade in staging..."
# Run staging tests

# 3. Execute upgrade/downgrade
echo "Executing upgrade to LTS..."
./upgrade-jenkins-core.sh $TARGET_LTS

echo "Weekly to LTS migration completed"
```

## Plugin Management During Upgrade

### Plugin Dependency Resolution
```groovy
// Plugin dependency checker
@Grab('org.jenkins-ci:version-number:1.8')
import hudson.PluginManager
import jenkins.model.Jenkins

def checkPluginDependencies() {
    def jenkins = Jenkins.instance
    def pluginManager = jenkins.pluginManager
    def dependencyIssues = []
    
    pluginManager.plugins.each { plugin ->
        if (!plugin.enabled) {
            return // Skip disabled plugins
        }
        
        plugin.dependencies.each { dependency ->
            def dependentPlugin = pluginManager.getPlugin(dependency.shortName)
            
            if (!dependentPlugin) {
                dependencyIssues << [
                    plugin: plugin.shortName,
                    missingDependency: dependency.shortName,
                    requiredVersion: dependency.version
                ]
            } else if (!dependency.version.equals(dependentPlugin.version)) {
                dependencyIssues << [
                    plugin: plugin.shortName,
                    dependency: dependency.shortName,
                    requiredVersion: dependency.version,
                    installedVersion: dependentPlugin.version
                ]
            }
        }
    }
    
    if (dependencyIssues.isEmpty()) {
        println "✓ No plugin dependency issues found"
    } else {
        println "✗ Plugin dependency issues found:"
        dependencyIssues.each { issue ->
            println "  ${issue.plugin} requires ${issue.dependency}:${issue.requiredVersion}"
            if (issue.installedVersion) {
                println "    Installed: ${issue.installedVersion}"
            } else {
                println "    Status: Missing"
            }
        }
    }
    
    return dependencyIssues
}

checkPluginDependencies()
```

## Monitoring During Upgrade

### Upgrade Monitoring Script
```bash
#!/bin/bash
# Jenkins upgrade monitoring

JENKINS_URL="http://localhost:8080"
LOG_FILE="/var/log/jenkins/jenkins.log"
MONITORING_DURATION=300  # 5 minutes

echo "Monitoring Jenkins upgrade..."

monitor_startup() {
    echo "Monitoring Jenkins startup..."
    local start_time=$(date +%s)
    local timeout=300  # 5 minutes
    
    while ! curl -s $JENKINS_URL/api/json > /dev/null; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ $elapsed -gt $timeout ]; then
            echo "✗ Jenkins startup timeout after ${timeout}s"
            return 1
        fi
        
        echo "Waiting for Jenkins... (${elapsed}s elapsed)"
        sleep 10
    done
    
    echo "✓ Jenkins started successfully"
    return 0
}

monitor_logs() {
    echo "Monitoring Jenkins logs for errors..."
    
    # Monitor for critical errors
    tail -f $LOG_FILE | while read line; do
        if [[ $line == *"ERROR"* ]] || [[ $line == *"SEVERE"* ]]; then
            echo "ERROR DETECTED: $line"
        elif [[ $line == *"WARNING"* ]]; then
            echo "WARNING: $line"
        elif [[ $line == *"Jenkins is fully up and running"* ]]; then
            echo "✓ Jenkins startup completed successfully"
            break
        fi
    done &
    
    # Monitor for specified duration
    sleep $MONITORING_DURATION
    kill $! 2>/dev/null
}

monitor_performance() {
    echo "Monitoring system performance..."
    
    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "CPU Usage: ${CPU_USAGE}%"
    
    # Memory usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f%%", $3/$2 * 100.0)}')
    echo "Memory Usage: $MEMORY_USAGE"
    
    # Disk usage
    DISK_USAGE=$(df -h /var/jenkins_home | awk 'NR==2{print $5}')
    echo "Disk Usage: $DISK_USAGE"
    
    # Jenkins-specific metrics
    JENKINS_MEMORY=$(curl -s $JENKINS_URL/manage/systemInfo | grep -A1 "Available memory" | tail -1 | tr -d ' ')
    echo "Jenkins Available Memory: $JENKINS_MEMORY"
}

# Execute monitoring
monitor_startup
if [ $? -eq 0 ]; then
    monitor_logs &
    monitor_performance
else
    echo "Jenkins startup failed. Check logs for details."
    tail -50 $LOG_FILE
fi
```

## Documentation Update Checklist

### Post-Upgrade Documentation
- [ ] Update Jenkins version in documentation
- [ ] Update plugin versions in documentation
- [ ] Update system requirements
- [ ] Update backup procedures
- [ ] Update monitoring configurations
- [ ] Update disaster recovery plans
- [ ] Update user guides and training materials
- [ ] Update integration documentation
- [ ] Update security procedures
- [ ] Update compliance documentation

### Communication Plan
- [ ] Notify stakeholders of upgrade completion
- [ ] Send upgrade summary report
- [ ] Schedule knowledge transfer sessions
- [ ] Update team communications channels
- [ ] Update support procedures
- [ ] Update escalation procedures

Remember: Jenkins upgrades should be thoroughly planned, tested, and validated. Always have a rollback plan ready and ensure all stakeholders are informed throughout the process.
"""