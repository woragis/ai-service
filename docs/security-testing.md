# Security Testing Guide

This guide explains security testing implementation for the AI Service, including SAST, DAST, and dependency scanning.

## Overview

Security testing is integrated into the CI/CD pipeline to identify vulnerabilities before deployment. Three types of security scans are performed:

1. **SAST (Static Application Security Testing)** - Code analysis
2. **Dependency Vulnerability Scanning** - Third-party library scanning
3. **Container Image Scanning** - Docker image security

## Security Scans

### 1. Bandit (SAST)

**What it does:** Scans Python code for common security issues.

**Issues detected:**
- SQL injection vulnerabilities
- Hardcoded passwords/secrets
- Insecure random number generation
- Use of insecure functions
- Missing security headers

**Configuration:**
- Scans: `app/` directory
- Output: JSON and text reports
- Severity levels: Low, Medium, High, Critical

**Running locally:**
```bash
pip install bandit
bandit -r app/ -f json -o bandit-report.json
bandit -r app/ -f txt
```

### 2. Safety (Dependency Scanning)

**What it does:** Scans Python dependencies for known vulnerabilities.

**Issues detected:**
- Known CVEs in dependencies
- Outdated packages with security issues
- Vulnerable package versions

**Configuration:**
- Scans: `requirements.txt`
- Output: JSON and text reports
- Uses: Safety DB (updated regularly)

**Running locally:**
```bash
pip install safety
safety check --json --output safety-report.json
safety check
```

### 3. pip-audit (Dependency Audit)

**What it does:** Alternative dependency scanner using PyPI Advisory Database.

**Issues detected:**
- CVEs in installed packages
- Vulnerable package versions
- Security advisories

**Configuration:**
- Scans: Installed packages
- Output: JSON and text reports
- Uses: PyPI Advisory Database

**Running locally:**
```bash
pip install pip-audit
pip-audit --format json --output pip-audit-report.json
pip-audit
```

## CI/CD Integration

Security tests run automatically in CI/CD on every push/PR. The workflow:

1. Installs security scanning tools
2. Runs Bandit (SAST)
3. Runs Safety (dependency scan)
4. Runs pip-audit (dependency audit)
5. Uploads reports as artifacts
6. Generates security report summary

### Viewing Results

Security reports are available in GitHub Actions artifacts:
- `bandit-report.json` - SAST results
- `safety-report.json` - Safety scan results
- `pip-audit-report.json` - pip-audit results

## Addressing Vulnerabilities

### High/Critical Severity

**Immediate action required:**
1. Review vulnerability details
2. Check if vulnerable code is in use
3. Update to patched version
4. Test thoroughly
5. Deploy fix

### Medium Severity

**Action within 1 week:**
1. Review vulnerability
2. Plan update
3. Test fix
4. Deploy in next release

### Low Severity

**Action within 1 month:**
1. Review vulnerability
2. Schedule update
3. Include in next release

## Best Practices

### 1. Regular Updates

- Update dependencies regularly
- Review security advisories
- Patch vulnerabilities promptly

### 2. Secure Coding

- Follow secure coding practices
- Avoid hardcoded secrets
- Use secure random number generation
- Validate and sanitize inputs

### 3. Dependency Management

- Pin dependency versions
- Review dependency changes
- Use trusted sources
- Minimize dependencies

### 4. Secrets Management

- Never commit secrets to code
- Use environment variables
- Use secret management services
- Rotate secrets regularly

### 5. Container Security

- Use minimal base images
- Keep images updated
- Scan images before deployment
- Use non-root users

## Security Checklist

Before deployment, ensure:

- [ ] No high/critical vulnerabilities
- [ ] Dependencies are up to date
- [ ] No hardcoded secrets
- [ ] Input validation in place
- [ ] Error handling doesn't leak information
- [ ] Security headers configured
- [ ] Authentication/authorization in place
- [ ] Rate limiting configured
- [ ] Logging doesn't expose sensitive data

## Container Image Scanning

### Trivy

Scan Docker images for vulnerabilities:

```bash
# Install Trivy
brew install trivy  # macOS
# or download from https://github.com/aquasecurity/trivy

# Scan image
trivy image woragis/ai-service:latest
```

### Docker Scout

```bash
# Scan image
docker scout cves woragis/ai-service:latest
```

## Dependency Updates

### Automated Updates

Use Dependabot for automated dependency updates:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

### Manual Updates

1. Review changelogs
2. Test updates locally
3. Run security scans
4. Update in staging
5. Deploy to production

## Security Incident Response

If a vulnerability is discovered:

1. **Assess**: Determine severity and impact
2. **Contain**: Limit exposure if possible
3. **Fix**: Develop and test fix
4. **Deploy**: Deploy fix quickly
5. **Monitor**: Watch for exploitation
6. **Document**: Record incident and response

## References

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)

