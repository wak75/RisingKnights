"""Jenkins security and compliance prompts."""


def register_prompts(mcp):
    """Register security and compliance prompts with the MCP server."""
    
    @mcp.prompt("jenkins_security_checklist")
    async def security_checklist() -> str:
        """
        Provide comprehensive Jenkins security checklist.
        
        Returns:
            Detailed security checklist for Jenkins
        """
        return """# Jenkins Security Checklist

## Initial Setup Security

### Installation Security
- [ ] Install Jenkins from official sources only
- [ ] Use latest LTS version
- [ ] Run Jenkins as dedicated non-root user
- [ ] Set proper file system permissions (750 for Jenkins home)
- [ ] Configure secure installation directory
- [ ] Disable Jenkins setup wizard in production

### Network Security
- [ ] Configure HTTPS with valid SSL certificates
- [ ] Disable HTTP access in production
- [ ] Configure proper firewall rules
- [ ] Use reverse proxy with security headers
- [ ] Implement rate limiting
- [ ] Block unnecessary ports from external access

## Authentication and Authorization

### User Management
- [ ] Enable Jenkins security (never run without security)
- [ ] Disable anonymous access
- [ ] Disable user signup
- [ ] Use centralized authentication (LDAP/AD/SSO)
- [ ] Implement strong password policies
- [ ] Enable two-factor authentication where possible
- [ ] Regular user access audits

### Authorization Strategy
- [ ] Use Matrix-based security or Project-based Matrix
- [ ] Follow principle of least privilege
- [ ] Use groups instead of individual permissions
- [ ] Regular permission audits
- [ ] Document permission structures
- [ ] Implement approval workflows for permission changes

### API Security
- [ ] Use API tokens instead of passwords
- [ ] Regular token rotation
- [ ] Limit token scope when possible
- [ ] Monitor API usage
- [ ] Implement API rate limiting
- [ ] Audit API access logs

## System Security

### Jenkins Core
- [ ] Keep Jenkins updated to latest LTS
- [ ] Subscribe to security advisories
- [ ] Test updates in staging first
- [ ] Monitor CVE databases
- [ ] Regular security assessments
- [ ] Implement automated update notifications

### Plugin Security
- [ ] Regular plugin updates
- [ ] Remove unused plugins
- [ ] Review plugin permissions
- [ ] Monitor plugin security advisories
- [ ] Use only trusted plugin sources
- [ ] Regular plugin audits

### Configuration Security
- [ ] Secure Jenkins configuration files
- [ ] Regular configuration backups
- [ ] Version control for configuration changes
- [ ] Implement Configuration as Code
- [ ] Secure credential storage
- [ ] Regular configuration reviews

## Build Security

### Pipeline Security
- [ ] Enable Script Security plugin
- [ ] Review and approve pipeline scripts
- [ ] Use shared libraries for trusted code
- [ ] Implement script approval workflow
- [ ] Regular script audits
- [ ] Sandbox untrusted code

### Credential Management
- [ ] Use Jenkins Credentials Store
- [ ] Encrypt credentials at rest
- [ ] Regular credential rotation
- [ ] Limit credential scope
- [ ] Audit credential usage
- [ ] Never hardcode secrets in pipelines

### Build Environment
- [ ] Use containerized builds when possible
- [ ] Implement build sandboxing
- [ ] Regular node security updates
- [ ] Monitor build resource usage
- [ ] Implement build timeouts
- [ ] Clean workspaces after builds

## Data Protection

### Backup Security
- [ ] Regular encrypted backups
- [ ] Secure backup storage
- [ ] Test backup restoration
- [ ] Document backup procedures
- [ ] Monitor backup integrity
- [ ] Implement backup retention policies

### Log Security
- [ ] Secure log file permissions
- [ ] Regular log rotation
- [ ] Monitor sensitive data in logs
- [ ] Implement log aggregation
- [ ] Secure log transmission
- [ ] Regular log audits

### Workspace Security
- [ ] Automatic workspace cleanup
- [ ] Secure workspace permissions
- [ ] Monitor workspace usage
- [ ] Implement workspace encryption
- [ ] Regular workspace audits
- [ ] Clean sensitive data from workspaces

## Monitoring and Auditing

### Security Monitoring
- [ ] Enable audit trail logging
- [ ] Monitor failed login attempts
- [ ] Set up security alerts
- [ ] Regular security log reviews
- [ ] Implement SIEM integration
- [ ] Monitor system resource usage

### Compliance Auditing
- [ ] Regular security assessments
- [ ] Document security procedures
- [ ] Implement compliance reporting
- [ ] Regular penetration testing
- [ ] Security training for administrators
- [ ] Maintain security documentation

### Incident Response
- [ ] Security incident response plan
- [ ] Regular incident response drills
- [ ] Emergency contact procedures
- [ ] Forensic data collection procedures
- [ ] Recovery procedures documented
- [ ] Post-incident review process

## Network and Infrastructure Security

### Network Security
- [ ] Use VPN for remote access
- [ ] Implement network segmentation
- [ ] Monitor network traffic
- [ ] Use secure protocols only
- [ ] Regular network security assessments
- [ ] Document network architecture

### Infrastructure Security
- [ ] Secure underlying operating system
- [ ] Regular OS security updates
- [ ] Implement host-based firewalls
- [ ] Monitor system integrity
- [ ] Use configuration management
- [ ] Regular infrastructure audits

## Compliance Requirements

### Regulatory Compliance
- [ ] Identify applicable regulations (SOX, HIPAA, PCI-DSS, etc.)
- [ ] Document compliance procedures
- [ ] Regular compliance assessments
- [ ] Implement required controls
- [ ] Maintain compliance documentation
- [ ] Regular compliance training

### Industry Standards
- [ ] Follow OWASP security guidelines
- [ ] Implement NIST cybersecurity framework
- [ ] Follow industry best practices
- [ ] Regular standards compliance reviews
- [ ] Document security standards adherence
- [ ] Keep up with standard updates

## Emergency Procedures

### Security Incidents
- [ ] Immediate containment procedures
- [ ] Evidence preservation procedures
- [ ] Communication protocols
- [ ] Recovery procedures
- [ ] Post-incident analysis
- [ ] Lessons learned documentation

### Disaster Recovery
- [ ] Business continuity plan
- [ ] Disaster recovery procedures
- [ ] Regular DR testing
- [ ] Recovery time objectives defined
- [ ] Recovery point objectives defined
- [ ] Alternative infrastructure ready

## Regular Security Tasks

### Daily Tasks
- [ ] Review security alerts
- [ ] Monitor failed login attempts
- [ ] Check system resource usage
- [ ] Review critical security logs
- [ ] Monitor backup status
- [ ] Check for security updates

### Weekly Tasks
- [ ] Review user access reports
- [ ] Check plugin update notifications
- [ ] Review security configurations
- [ ] Monitor compliance status
- [ ] Review incident reports
- [ ] Update security documentation

### Monthly Tasks
- [ ] Full security log review
- [ ] User access audit
- [ ] Plugin security review
- [ ] Configuration change review
- [ ] Security metrics reporting
- [ ] Security training updates

### Quarterly Tasks
- [ ] Comprehensive security assessment
- [ ] Penetration testing
- [ ] Security policy review
- [ ] Disaster recovery testing
- [ ] Compliance audit
- [ ] Security training sessions

### Annual Tasks
- [ ] Full security audit
- [ ] Risk assessment update
- [ ] Security policy updates
- [ ] Infrastructure security review
- [ ] Compliance certification renewal
- [ ] Security strategy review

## Security Tools and Resources

### Recommended Security Tools
- [ ] Security scanning tools
- [ ] Vulnerability assessment tools
- [ ] Log analysis tools
- [ ] Monitoring and alerting systems
- [ ] Backup and recovery tools
- [ ] Configuration management tools

### Security Resources
- [ ] Jenkins Security Advisory mailing list
- [ ] OWASP Jenkins security guide
- [ ] NIST cybersecurity resources
- [ ] Industry security forums
- [ ] Security training materials
- [ ] Compliance documentation

## Documentation Requirements

### Security Documentation
- [ ] Security policies and procedures
- [ ] User access matrix
- [ ] Network architecture diagrams
- [ ] Incident response procedures
- [ ] Recovery procedures
- [ ] Security training materials

### Compliance Documentation
- [ ] Compliance requirements matrix
- [ ] Control implementation evidence
- [ ] Audit trail documentation
- [ ] Risk assessment reports
- [ ] Security test results
- [ ] Compliance training records

Remember: Security is an ongoing process, not a one-time setup. Regular reviews, updates, and improvements are essential for maintaining a secure Jenkins environment.
"""
    
    @mcp.prompt("jenkins_compliance_guidelines")
    async def compliance_guidelines() -> str:
        """
        Provide Jenkins compliance guidelines for various regulations.
        
        Returns:
            Detailed compliance guidelines for Jenkins
        """
        return """# Jenkins Compliance Guidelines

## SOX (Sarbanes-Oxley) Compliance

### Control Requirements
**Access Controls:**
```groovy
// Implement segregation of duties
authorization {
    permission('hudson.model.Item.Build', 'developer-group')
    permission('hudson.model.Item.Configure', 'admin-group')
    permission('hudson.model.Item.Delete', 'admin-group')
    permission('hudson.model.Hudson.Administer', 'sox-admin-group')
}
```

**Change Management:**
- All pipeline changes must be approved
- Version control for all job configurations
- Audit trail for all changes
- Documentation of change rationale

**Data Integrity:**
```groovy
pipeline {
    stages {
        stage('SOX Controls') {
            steps {
                // Data validation
                sh 'validate-financial-data.sh'
                
                // Audit logging
                script {
                    def auditLog = [
                        timestamp: new Date(),
                        user: env.BUILD_USER,
                        action: 'financial-build',
                        jobName: env.JOB_NAME,
                        buildNumber: env.BUILD_NUMBER
                    ]
                    writeJSON file: 'audit.json', json: auditLog
                }
            }
        }
    }
}
```

### Documentation Requirements
- [ ] Document all automated controls
- [ ] Maintain change logs
- [ ] Regular access reviews
- [ ] Control testing evidence
- [ ] Exception documentation

## HIPAA Compliance

### Data Protection Requirements
```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
              spec:
                containers:
                - name: secure-build
                  image: hipaa-compliant-image
                  securityContext:
                    runAsNonRoot: true
                    readOnlyRootFilesystem: true
            '''
        }
    }
    
    stages {
        stage('HIPAA Controls') {
            steps {
                // Encrypt PHI data
                sh 'encrypt-phi-data.sh'
                
                // Access logging
                sh '''
                    echo "$(date): ${BUILD_USER} accessed PHI data in ${JOB_NAME}" >> /var/log/phi-access.log
                '''
                
                // Data masking for logs
                sh 'mask-sensitive-data.sh'
            }
        }
    }
    
    post {
        always {
            // Secure cleanup
            sh 'secure-cleanup.sh'
            deleteDir()
        }
    }
}
```

### Access Controls
- [ ] Minimum necessary access principle
- [ ] User authentication and authorization
- [ ] Automatic session timeouts
- [ ] Access logging and monitoring
- [ ] Regular access reviews

### Technical Safeguards
- [ ] Data encryption in transit and at rest
- [ ] Secure workspaces
- [ ] Audit trails
- [ ] Automatic logoff
- [ ] Data backup and recovery

## PCI-DSS Compliance

### Network Security
```bash
# Firewall configuration for PCI compliance
iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# Secure Jenkins configuration
JAVA_OPTS="$JAVA_OPTS -Dhudson.security.csrf.DefaultCrumbIssuer.EXCLUDE_SESSION_ID=true"
JAVA_OPTS="$JAVA_OPTS -Djenkins.security.seed.UserSeedProperty.disableUserSeed=false"
```

### Data Protection
```groovy
pipeline {
    stages {
        stage('PCI Controls') {
            steps {
                // Cardholder data detection
                sh 'scan-for-card-data.sh'
                
                // Tokenization
                sh 'tokenize-sensitive-data.sh'
                
                // Secure transmission
                withCredentials([string(credentialsId: 'payment-api-key', variable: 'API_KEY')]) {
                    sh 'curl -H "Authorization: Bearer $API_KEY" https://secure-payment-api.com/process'
                }
            }
        }
    }
}
```

### Compliance Controls
- [ ] Regular vulnerability scans
- [ ] Network segmentation
- [ ] Strong access controls
- [ ] Regular monitoring and testing
- [ ] Secure development practices

## GDPR Compliance

### Data Privacy Controls
```groovy
pipeline {
    stages {
        stage('GDPR Compliance') {
            steps {
                // Data classification
                sh 'classify-personal-data.sh'
                
                // Privacy impact assessment
                sh 'privacy-impact-assessment.sh'
                
                // Data minimization
                sh 'minimize-data-collection.sh'
                
                // Consent management
                script {
                    if (params.DATA_PROCESSING_CONSENT == 'true') {
                        sh 'process-personal-data.sh'
                    } else {
                        echo 'Skipping personal data processing - no consent'
                    }
                }
            }
        }
    }
}
```

### Data Subject Rights
- [ ] Right to access (data portability)
- [ ] Right to rectification
- [ ] Right to erasure (right to be forgotten)
- [ ] Right to restrict processing
- [ ] Right to object
- [ ] Data breach notification procedures

### Technical Measures
```groovy
// Data anonymization
stage('Anonymize Data') {
    steps {
        sh 'anonymize-personal-data.sh'
        sh 'verify-anonymization.sh'
    }
}

// Data retention
stage('Data Retention') {
    steps {
        script {
            def retentionPolicy = readJSON file: 'retention-policy.json'
            sh "cleanup-data-older-than.sh ${retentionPolicy.maxRetentionDays}"
        }
    }
}
```

## FDA 21 CFR Part 11 (Life Sciences)

### Electronic Records Requirements
```groovy
pipeline {
    options {
        // Ensure build records are preserved
        buildDiscarder(logRotator(numToKeepStr: '999999'))
    }
    
    stages {
        stage('FDA Controls') {
            steps {
                // Digital signatures
                sh 'sign-build-artifacts.sh'
                
                // Audit trail
                script {
                    def auditRecord = [
                        timestamp: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'"),
                        user: env.BUILD_USER,
                        userRole: env.BUILD_USER_ROLE,
                        action: 'manufacturing-build',
                        jobName: env.JOB_NAME,
                        buildNumber: env.BUILD_NUMBER,
                        signature: sh(script: 'generate-digital-signature.sh', returnStdout: true).trim()
                    ]
                    writeJSON file: "fda-audit-${env.BUILD_NUMBER}.json", json: auditRecord
                }
                
                // Record integrity checks
                sh 'verify-record-integrity.sh'
            }
        }
    }
}
```

### Validation Requirements
- [ ] Computer system validation (CSV)
- [ ] User access controls
- [ ] Audit trail review procedures
- [ ] Electronic signature controls
- [ ] System security controls

## ISO 27001 Compliance

### Information Security Management
```groovy
// Security controls implementation
pipeline {
    stages {
        stage('ISO 27001 Controls') {
            steps {
                // Asset classification
                sh 'classify-information-assets.sh'
                
                // Risk assessment
                sh 'assess-security-risks.sh'
                
                // Security monitoring
                sh 'monitor-security-events.sh'
                
                // Incident management
                script {
                    if (currentBuild.result == 'FAILURE') {
                        sh 'trigger-security-incident-response.sh'
                    }
                }
            }
        }
    }
}
```

### Control Objectives
- [ ] Information security policies
- [ ] Organization of information security
- [ ] Human resource security
- [ ] Asset management
- [ ] Access control
- [ ] Cryptography
- [ ] Physical and environmental security
- [ ] Operations security
- [ ] Communications security
- [ ] System acquisition, development and maintenance
- [ ] Supplier relationships
- [ ] Information security incident management
- [ ] Business continuity management
- [ ] Compliance

## Common Compliance Patterns

### Audit Trail Implementation
```groovy
@NonCPS
def logComplianceEvent(eventType, details) {
    def timestamp = new Date().format("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
    def logEntry = [
        timestamp: timestamp,
        eventType: eventType,
        jobName: env.JOB_NAME,
        buildNumber: env.BUILD_NUMBER,
        user: env.BUILD_USER ?: 'system',
        nodeLabel: env.NODE_LABELS,
        details: details
    ]
    
    // Write to compliance log
    writeJSON file: "compliance-log-${timestamp}.json", json: logEntry
    
    // Send to SIEM system
    sh "curl -X POST https://siem.company.com/api/events -d '${groovy.json.JsonOutput.toJson(logEntry)}'"
}

pipeline {
    stages {
        stage('Compliance Logging') {
            steps {
                script {
                    logComplianceEvent('BUILD_START', [
                        repository: env.GIT_URL,
                        branch: env.GIT_BRANCH,
                        commit: env.GIT_COMMIT
                    ])
                }
            }
        }
    }
    
    post {
        always {
            script {
                logComplianceEvent('BUILD_END', [
                    result: currentBuild.result,
                    duration: currentBuild.duration
                ])
            }
        }
    }
}
```

### Change Control Process
```groovy
pipeline {
    stages {
        stage('Change Control') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Require approval for production changes
                    def approvers = ['compliance-officer', 'security-admin', 'qa-lead']
                    def approvalRequired = true
                    
                    if (approvalRequired) {
                        input message: 'Production deployment requires approval',
                              submitterParameter: 'APPROVER',
                              parameters: [
                                  choice(name: 'APPROVAL_TYPE', 
                                        choices: ['Standard Change', 'Emergency Change', 'Normal Change'],
                                        description: 'Type of change'),
                                  text(name: 'CHANGE_DESCRIPTION',
                                       description: 'Describe the change and business justification'),
                                  text(name: 'ROLLBACK_PLAN',
                                       description: 'Describe the rollback plan')
                              ]
                    }
                    
                    // Log the approval
                    logComplianceEvent('CHANGE_APPROVED', [
                        approver: env.APPROVER,
                        approvalType: params.APPROVAL_TYPE,
                        description: params.CHANGE_DESCRIPTION,
                        rollbackPlan: params.ROLLBACK_PLAN
                    ])
                }
            }
        }
    }
}
```

### Data Lifecycle Management
```groovy
pipeline {
    stages {
        stage('Data Lifecycle') {
            steps {
                script {
                    // Data classification
                    def dataClassification = sh(
                        script: 'classify-data.sh', 
                        returnStdout: true
                    ).trim()
                    
                    // Apply retention policies
                    switch(dataClassification) {
                        case 'public':
                            env.RETENTION_DAYS = '90'
                            break
                        case 'internal':
                            env.RETENTION_DAYS = '365'
                            break
                        case 'confidential':
                            env.RETENTION_DAYS = '2555' // 7 years
                            break
                        case 'restricted':
                            env.RETENTION_DAYS = '3650' // 10 years
                            break
                    }
                    
                    // Set build retention
                    properties([
                        buildDiscarder(logRotator(daysToKeepStr: env.RETENTION_DAYS))
                    ])
                }
                
                // Secure data handling
                sh 'handle-data-securely.sh'
            }
        }
    }
}
```

## Compliance Reporting

### Automated Compliance Reports
```groovy
pipeline {
    triggers {
        cron('0 0 * * 0') // Weekly compliance report
    }
    
    stages {
        stage('Generate Compliance Report') {
            steps {
                script {
                    // Collect compliance metrics
                    def report = [
                        reportDate: new Date().format("yyyy-MM-dd"),
                        totalBuilds: sh(script: 'count-builds.sh', returnStdout: true).trim(),
                        failedBuilds: sh(script: 'count-failed-builds.sh', returnStdout: true).trim(),
                        securityViolations: sh(script: 'count-security-violations.sh', returnStdout: true).trim(),
                        accessViolations: sh(script: 'count-access-violations.sh', returnStdout: true).trim(),
                        dataBreaches: sh(script: 'count-data-breaches.sh', returnStdout: true).trim()
                    ]
                    
                    // Generate report
                    writeJSON file: 'compliance-report.json', json: report
                    sh 'generate-compliance-dashboard.sh'
                }
                
                // Archive report
                archiveArtifacts artifacts: 'compliance-report.json,compliance-dashboard.html'
                
                // Send to compliance team
                emailext (
                    subject: "Weekly Compliance Report - ${new Date().format('yyyy-MM-dd')}",
                    body: "Please find the attached compliance report.",
                    attachments: 'compliance-report.json,compliance-dashboard.html',
                    to: 'compliance@company.com'
                )
            }
        }
    }
}
```

## Best Practices Summary

### Documentation
- [ ] Maintain compliance documentation
- [ ] Regular policy updates
- [ ] Training materials
- [ ] Procedure documentation
- [ ] Evidence collection processes

### Monitoring
- [ ] Continuous compliance monitoring
- [ ] Automated compliance checks
- [ ] Regular compliance assessments
- [ ] Violation reporting
- [ ] Corrective action tracking

### Governance
- [ ] Compliance committee
- [ ] Regular compliance reviews
- [ ] Risk assessments
- [ ] Change control processes
- [ ] Incident response procedures

Remember: Compliance requirements vary by industry and jurisdiction. Always consult with your legal and compliance teams to ensure your Jenkins implementation meets all applicable requirements.
"""