# Alerting Guide

This guide explains how to set up and manage Prometheus alerting for the AI Service.

## Overview

Alerting is configured using Prometheus alerting rules that monitor service metrics and trigger alerts when thresholds are exceeded. Alerts are sent to Alertmanager, which routes them to notification channels (email, Slack, PagerDuty, etc.).

## Alert Configuration

Alert rules are defined in `monitoring/alerts.yml`. This file contains all alert definitions for the AI Service.

### Alert Rules

The following alerts are configured:

#### Critical Alerts

1. **HighErrorRate** - Triggers when error rate exceeds 1% for 5 minutes
   - Severity: `critical`
   - Threshold: > 1% error rate
   - Duration: 5 minutes

2. **ServiceDown** - Triggers when service is unreachable
   - Severity: `critical`
   - Condition: Service down for > 1 minute

3. **LowAvailability** - Triggers when availability drops below SLO target
   - Severity: `critical`
   - Threshold: < 99.9% availability
   - Duration: 10 minutes

4. **ErrorBudgetDepletion** - Triggers when error budget is being depleted
   - Severity: `critical`
   - Threshold: > 0.1% error rate over 30 days
   - Duration: 1 hour

#### Warning Alerts

1. **HighLatencyP95** - Triggers when P95 latency exceeds 500ms
   - Severity: `warning`
   - Threshold: > 500ms P95 latency
   - Duration: 5 minutes

2. **HighLatencyP99** - Triggers when P99 latency exceeds 1000ms
   - Severity: `warning`
   - Threshold: > 1000ms P99 latency
   - Duration: 5 minutes

3. **HighRequestRate** - Triggers when request rate exceeds 1000 req/s
   - Severity: `warning`
   - Threshold: > 1000 req/s
   - Duration: 5 minutes

4. **HighMemoryUsage** - Triggers when memory usage exceeds 512MB
   - Severity: `warning`
   - Threshold: > 512MB
   - Duration: 5 minutes

5. **HighCPUUsage** - Triggers when CPU usage exceeds 80%
   - Severity: `warning`
   - Threshold: > 80% CPU
   - Duration: 5 minutes

6. **ExternalAPIFailure** - Triggers when external API calls fail
   - Severity: `critical`
   - Condition: Chat endpoint errors > 0
   - Duration: 5 minutes

## Setup

### 1. Configure Prometheus

Add the alert rules to your Prometheus configuration:

```yaml
# prometheus.yml
rule_files:
  - "monitoring/alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Configure Alertmanager

Set up Alertmanager to route alerts to notification channels:

```yaml
# alertmanager.yml
route:
  receiver: 'default-receiver'
  routes:
    - match:
        severity: critical
      receiver: 'critical-receiver'
    - match:
        severity: warning
      receiver: 'warning-receiver'

receivers:
  - name: 'default-receiver'
    email_configs:
      - to: 'team@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.example.com:587'
  
  - name: 'critical-receiver'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
  
  - name: 'warning-receiver'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-warning'
```

### 3. Deploy Alertmanager

Deploy Alertmanager in your Kubernetes cluster:

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:latest
        ports:
        - containerPort: 9093
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
EOF
```

## Alert Management

### Viewing Active Alerts

View active alerts in Prometheus UI:
```
http://prometheus:9090/alerts
```

View alerts in Alertmanager UI:
```
http://alertmanager:9093
```

### Testing Alerts

Test alerts by temporarily lowering thresholds or simulating failures:

```bash
# Simulate high error rate
# (This would require modifying the service to return errors)

# Check alert status
curl http://prometheus:9090/api/v1/alerts
```

### Alert Runbooks

Each alert should have a corresponding runbook with:
- What the alert means
- How to investigate
- How to resolve
- Escalation procedures

Example runbook for HighErrorRate:
1. Check service logs: `kubectl logs -f deployment/ai-service`
2. Check metrics: `curl http://ai-service:8080/metrics`
3. Check external dependencies (OpenAI, Anthropic APIs)
4. Check recent deployments
5. Rollback if needed: `kubectl rollout undo deployment/ai-service`

## Best Practices

1. **Alert Fatigue**: Avoid too many alerts. Only alert on actionable issues.
2. **Alert Grouping**: Group related alerts to reduce noise.
3. **Alert Suppression**: Suppress alerts during maintenance windows.
4. **Alert Acknowledgment**: Acknowledge alerts when investigating.
5. **Runbooks**: Maintain runbooks for each alert type.
6. **Testing**: Regularly test alerting to ensure it works.
7. **Review**: Periodically review and tune alert thresholds.

## Troubleshooting

### Alerts Not Firing

1. Check Prometheus is scraping metrics: `curl http://prometheus:9090/api/v1/targets`
2. Check alert rules are loaded: `curl http://prometheus:9090/api/v1/rules`
3. Check Alertmanager is receiving alerts: `curl http://alertmanager:9093/api/v2/alerts`

### Too Many Alerts

1. Review alert thresholds - they may be too sensitive
2. Increase alert duration to reduce false positives
3. Group related alerts together
4. Suppress alerts during known issues

### Alerts Not Reaching Notification Channels

1. Check Alertmanager configuration
2. Test notification channels independently
3. Check network connectivity
4. Verify credentials/API keys

## References

- [Prometheus Alerting Documentation](https://prometheus.io/docs/alerting/latest/overview/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)

