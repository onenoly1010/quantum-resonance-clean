# 📊 TELEMETRY: Metrics, Monitoring, and Alerting

## Overview

The Quantum Resonance telemetry system provides real-time monitoring, alerting, and performance tracking for all forge operations.

## Core Metrics

### System Health Metrics
| Metric | Description | Unit | Alert Threshold |
|--------|-------------|------|-----------------|
| `cpu_usage` | CPU utilization percentage | % | > 80% |
| `memory_usage` | RAM consumption | MB | > 1024 MB |
| `disk_usage` | Storage utilization | GB | > 8 GB |
| `uptime` | System uptime | seconds | < 60 (unexpected restart) |
| `error_rate` | Application errors per minute | count/min | > 5 |

### API Performance Metrics
| Metric | Description | Unit | Alert Threshold |
|--------|-------------|------|-----------------|
| `api_response_time` | Average API response latency | ms | > 2000 ms |
| `api_request_count` | Total API requests | count | N/A |
| `api_error_rate` | Failed API requests | % | > 5% |
| `huggingface_latency` | HF model inference time | ms | > 5000 ms |
| `pi_sdk_latency` | Pi Network SDK call time | ms | > 3000 ms |

### Business Metrics
| Metric | Description | Unit | Alert Threshold |
|--------|-------------|------|-----------------|
| `active_users` | Currently active users | count | N/A |
| `transactions_completed` | Successful Pi transactions | count | N/A |
| `mining_boost_active` | Mining boost status | boolean | false |
| `wallet_balance` | Current wallet balance | Pi | < 10 Pi |
| `community_resonance` | Community engagement score | 0-100 | < 20 |

## Alert Thresholds

### Critical Alerts (Immediate Response Required)
- **System Down**: Uptime < 60 seconds
- **Wallet Compromised**: Unauthorized transaction detected
- **Error Storm**: Error rate > 20/minute
- **Out of Memory**: Memory usage > 95%
- **API Failure**: Error rate > 20%

### Warning Alerts (Review Within 1 Hour)
- **High CPU**: CPU usage > 80%
- **High Memory**: Memory usage > 80%
- **Slow API**: Response time > 2000ms
- **Low Balance**: Wallet balance < 10 Pi
- **Mining Boost Inactive**: mining_boost_active = false

### Info Alerts (Review Daily)
- **Moderate CPU**: CPU usage > 60%
- **Slow Inference**: HF latency > 3000ms
- **Low Resonance**: Community score < 40

## Webhook Integration

### Webhook Event Format
```json
{
  "event_type": "alert.triggered",
  "severity": "critical",
  "timestamp": "2025-12-11T01:54:16Z",
  "metric": "error_rate",
  "current_value": 25,
  "threshold": 5,
  "message": "Error rate exceeded threshold: 25 errors/min (threshold: 5)",
  "metadata": {
    "service": "quantum-resonance-api",
    "environment": "production",
    "region": "us-east-1"
  }
}
```

### Webhook Endpoints

#### Discord Webhook
```bash
curl -X POST "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🚨 **CRITICAL ALERT**",
    "embeds": [{
      "title": "Error Rate Threshold Exceeded",
      "description": "Error rate: 25/min (threshold: 5/min)",
      "color": 16711680,
      "fields": [
        {"name": "Service", "value": "quantum-resonance-api", "inline": true},
        {"name": "Time", "value": "2025-12-11T01:54:16Z", "inline": true}
      ]
    }]
  }'
```

#### Slack Webhook
```bash
curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🚨 CRITICAL ALERT: Error Rate Exceeded",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Error Rate Threshold Exceeded*\nCurrent: 25/min | Threshold: 5/min"
        }
      },
      {
        "type": "section",
        "fields": [
          {"type": "mrkdwn", "text": "*Service:*\nquantum-resonance-api"},
          {"type": "mrkdwn", "text": "*Time:*\n2025-12-11T01:54:16Z"}
        ]
      }
    ]
  }'
```

#### Custom HTTP Endpoint
```bash
curl -X POST "https://your-telemetry-hub.com/api/alerts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "event_type": "alert.triggered",
    "severity": "critical",
    "metric": "error_rate",
    "current_value": 25,
    "threshold": 5
  }'
```

## HUB_LOG_STREAM Example

### Real-Time Log Stream Configuration
```python
import asyncio
import json
from datetime import datetime

class HubLogStream:
    """Real-time telemetry log streaming to central hub"""
    
    def __init__(self, hub_url, api_key):
        self.hub_url = hub_url
        self.api_key = api_key
        self.buffer = []
        self.buffer_size = 100
        
    async def log(self, level, message, metadata=None):
        """Log event to stream"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "metadata": metadata or {},
            "service": "quantum-resonance"
        }
        
        self.buffer.append(entry)
        
        if len(self.buffer) >= self.buffer_size:
            await self.flush()
    
    async def flush(self):
        """Flush buffer to hub"""
        if not self.buffer:
            return
            
        try:
            # Send to telemetry hub
            payload = {
                "logs": self.buffer,
                "source": "quantum-resonance-clean"
            }
            
            # Simulated HTTP POST (replace with actual implementation)
            print(f"📡 Streaming {len(self.buffer)} logs to hub...")
            print(json.dumps(payload, indent=2))
            
            self.buffer = []
        except Exception as e:
            print(f"❌ Failed to flush logs: {e}")

# Usage Example
async def main():
    stream = HubLogStream(
        hub_url="https://telemetry-hub.example.com/api/logs",
        api_key="your_secure_api_key"
    )
    
    # Log various events
    await stream.log("INFO", "System initialized", {"version": "1.0.0"})
    await stream.log("WARNING", "High CPU usage detected", {"cpu": 85})
    await stream.log("ERROR", "API request failed", {
        "endpoint": "/api/inference",
        "status_code": 500
    })
    
    # Force flush
    await stream.flush()

# Run example
# asyncio.run(main())
```

### Sample Log Output
```json
{
  "logs": [
    {
      "timestamp": "2025-12-11T01:54:16.123Z",
      "level": "INFO",
      "message": "System initialized",
      "metadata": {"version": "1.0.0"},
      "service": "quantum-resonance"
    },
    {
      "timestamp": "2025-12-11T01:54:17.456Z",
      "level": "WARNING",
      "message": "High CPU usage detected",
      "metadata": {"cpu": 85},
      "service": "quantum-resonance"
    },
    {
      "timestamp": "2025-12-11T01:54:18.789Z",
      "level": "ERROR",
      "message": "API request failed",
      "metadata": {
        "endpoint": "/api/inference",
        "status_code": 500
      },
      "service": "quantum-resonance"
    }
  ],
  "source": "quantum-resonance-clean"
}
```

## Monitoring Dashboard

### Key Visualizations
1. **System Health**: Real-time CPU, memory, disk usage
2. **API Performance**: Response times, error rates, throughput
3. **User Activity**: Active users, transaction volume
4. **Pi Network**: Wallet balance, mining boost status
5. **Alert Timeline**: Recent alerts and resolutions

### Recommended Tools
- **Grafana**: Dashboard visualization
- **Prometheus**: Metrics collection
- **Loki**: Log aggregation
- **AlertManager**: Alert routing and management

## Integration with Forge Rituals

Telemetry is integrated into the daily ritual cadence:

- **Morning Resonance**: Review overnight metrics and alerts
- **Evening Broadcast**: Publish daily telemetry summary
- **Weekly Audit**: Analyze trends and optimize thresholds
- **Monthly Review**: Update metrics and alert configurations

---

*"What gets measured gets managed, what gets monitored gets optimized."*
