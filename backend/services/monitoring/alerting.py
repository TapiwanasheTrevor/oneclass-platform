"""
Alerting System
Advanced alerting and notification system for monitoring
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from shared.config import settings
from .service import monitoring_service
from .schemas import AlertCreate, Severity, AlertStatus

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


class AlertCondition(str, Enum):
    """Alert conditions"""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"


class AlertRule(BaseModel):
    """Alert rule configuration"""
    name: str
    description: str
    metric_name: str
    condition: AlertCondition
    threshold: float
    duration: int  # seconds
    severity: Severity
    enabled: bool = True
    notification_channels: List[NotificationChannel] = []
    tags: Optional[Dict[str, Any]] = None
    cooldown_period: int = 300  # 5 minutes default


class NotificationTarget(BaseModel):
    """Notification target configuration"""
    channel: NotificationChannel
    config: Dict[str, Any]
    enabled: bool = True


class AlertingService:
    """Main alerting service"""
    
    def __init__(self):
        self.alert_rules: List[AlertRule] = []
        self.notification_targets: List[NotificationTarget] = []
        self.alert_states: Dict[str, Dict[str, Any]] = {}
        self.cooldown_tracker: Dict[str, datetime] = {}
        self._load_default_rules()
        self._load_notification_targets()
    
    def _load_default_rules(self):
        """Load default alert rules"""
        default_rules = [
            AlertRule(
                name="High CPU Usage",
                description="CPU usage exceeds 80%",
                metric_name="system.cpu_usage",
                condition=AlertCondition.GREATER_THAN,
                threshold=80.0,
                duration=300,
                severity=Severity.WARNING,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
            ),
            AlertRule(
                name="Critical CPU Usage",
                description="CPU usage exceeds 95%",
                metric_name="system.cpu_usage",
                condition=AlertCondition.GREATER_THAN,
                threshold=95.0,
                duration=60,
                severity=Severity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS]
            ),
            AlertRule(
                name="High Memory Usage",
                description="Memory usage exceeds 85%",
                metric_name="system.memory_usage",
                condition=AlertCondition.GREATER_THAN,
                threshold=85.0,
                duration=300,
                severity=Severity.WARNING,
                notification_channels=[NotificationChannel.EMAIL]
            ),
            AlertRule(
                name="Critical Memory Usage",
                description="Memory usage exceeds 95%",
                metric_name="system.memory_usage",
                condition=AlertCondition.GREATER_THAN,
                threshold=95.0,
                duration=60,
                severity=Severity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS]
            ),
            AlertRule(
                name="High Error Rate",
                description="Error rate exceeds 5%",
                metric_name="http.error_rate",
                condition=AlertCondition.GREATER_THAN,
                threshold=5.0,
                duration=300,
                severity=Severity.WARNING,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
            ),
            AlertRule(
                name="Database Connection Issues",
                description="Database connection count exceeds 100",
                metric_name="database.connection_count",
                condition=AlertCondition.GREATER_THAN,
                threshold=100.0,
                duration=180,
                severity=Severity.ERROR,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
            ),
            AlertRule(
                name="Slow Response Time",
                description="Average response time exceeds 2000ms",
                metric_name="http.response_time",
                condition=AlertCondition.GREATER_THAN,
                threshold=2000.0,
                duration=300,
                severity=Severity.WARNING,
                notification_channels=[NotificationChannel.EMAIL]
            ),
            AlertRule(
                name="Service Down",
                description="Service health check failed",
                metric_name="service.health",
                condition=AlertCondition.EQUALS,
                threshold=0.0,  # 0 = unhealthy, 1 = healthy
                duration=60,
                severity=Severity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS]
            )
        ]
        
        self.alert_rules = default_rules
    
    def _load_notification_targets(self):
        """Load notification targets from configuration"""
        notification_targets = []
        
        # Email notifications
        if hasattr(settings, 'SMTP_SERVER') and settings.SMTP_SERVER:
            notification_targets.append(NotificationTarget(
                channel=NotificationChannel.EMAIL,
                config={
                    "smtp_server": settings.SMTP_SERVER,
                    "smtp_port": getattr(settings, 'SMTP_PORT', 587),
                    "username": getattr(settings, 'SMTP_USERNAME', ''),
                    "password": getattr(settings, 'SMTP_PASSWORD', ''),
                    "from_email": getattr(settings, 'ALERT_FROM_EMAIL', 'alerts@oneclass.ac.zw'),
                    "to_emails": getattr(settings, 'ALERT_TO_EMAILS', ['admin@oneclass.ac.zw'])
                }
            ))
        
        # Slack notifications
        if hasattr(settings, 'SLACK_WEBHOOK_URL') and settings.SLACK_WEBHOOK_URL:
            notification_targets.append(NotificationTarget(
                channel=NotificationChannel.SLACK,
                config={
                    "webhook_url": settings.SLACK_WEBHOOK_URL,
                    "channel": getattr(settings, 'SLACK_CHANNEL', '#alerts'),
                    "username": getattr(settings, 'SLACK_USERNAME', 'OneClass Alerts')
                }
            ))
        
        # Webhook notifications
        if hasattr(settings, 'ALERT_WEBHOOK_URL') and settings.ALERT_WEBHOOK_URL:
            notification_targets.append(NotificationTarget(
                channel=NotificationChannel.WEBHOOK,
                config={
                    "webhook_url": settings.ALERT_WEBHOOK_URL,
                    "headers": getattr(settings, 'ALERT_WEBHOOK_HEADERS', {}),
                    "timeout": getattr(settings, 'ALERT_WEBHOOK_TIMEOUT', 30)
                }
            ))
        
        self.notification_targets = notification_targets
    
    async def evaluate_rules(self, metric_name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Evaluate alert rules for a metric"""
        try:
            for rule in self.alert_rules:
                if not rule.enabled:
                    continue
                
                if rule.metric_name != metric_name:
                    continue
                
                # Check if rule matches
                if await self._evaluate_condition(rule, value):
                    await self._handle_alert_triggered(rule, value, tags)
                else:
                    await self._handle_alert_resolved(rule, value, tags)
        
        except Exception as e:
            logger.error(f"Failed to evaluate alert rules: {str(e)}")
    
    async def _evaluate_condition(self, rule: AlertRule, value: float) -> bool:
        """Evaluate if a condition is met"""
        if rule.condition == AlertCondition.GREATER_THAN:
            return value > rule.threshold
        elif rule.condition == AlertCondition.LESS_THAN:
            return value < rule.threshold
        elif rule.condition == AlertCondition.EQUALS:
            return value == rule.threshold
        elif rule.condition == AlertCondition.NOT_EQUALS:
            return value != rule.threshold
        else:
            return False
    
    async def _handle_alert_triggered(self, rule: AlertRule, value: float, tags: Optional[Dict[str, Any]]) -> None:
        """Handle when an alert is triggered"""
        try:
            alert_key = f"{rule.name}_{rule.metric_name}"
            current_time = datetime.utcnow()
            
            # Check if alert is in cooldown
            if alert_key in self.cooldown_tracker:
                last_alert = self.cooldown_tracker[alert_key]
                if (current_time - last_alert).total_seconds() < rule.cooldown_period:
                    return
            
            # Check if alert state exists
            if alert_key not in self.alert_states:
                self.alert_states[alert_key] = {
                    "first_triggered": current_time,
                    "last_triggered": current_time,
                    "triggered_count": 1,
                    "state": "triggered"
                }
            else:
                self.alert_states[alert_key]["last_triggered"] = current_time
                self.alert_states[alert_key]["triggered_count"] += 1
            
            # Check if duration threshold is met
            alert_state = self.alert_states[alert_key]
            duration_seconds = (current_time - alert_state["first_triggered"]).total_seconds()
            
            if duration_seconds >= rule.duration:
                # Create alert
                alert_data = AlertCreate(
                    alert_name=rule.name,
                    alert_type="metric_threshold",
                    severity=rule.severity,
                    description=f"{rule.description}. Current value: {value}, Threshold: {rule.threshold}",
                    metric_name=rule.metric_name,
                    threshold_value=rule.threshold,
                    current_value=value,
                    condition=rule.condition,
                    tags=tags or {}
                )
                
                alert_id = await monitoring_service.create_alert(alert_data)
                
                # Send notifications
                await self._send_notifications(rule, alert_data, value)
                
                # Update cooldown tracker
                self.cooldown_tracker[alert_key] = current_time
                
                logger.info(f"Alert triggered: {rule.name} - {value} {rule.condition} {rule.threshold}")
        
        except Exception as e:
            logger.error(f"Failed to handle alert triggered: {str(e)}")
    
    async def _handle_alert_resolved(self, rule: AlertRule, value: float, tags: Optional[Dict[str, Any]]) -> None:
        """Handle when an alert is resolved"""
        try:
            alert_key = f"{rule.name}_{rule.metric_name}"
            
            if alert_key in self.alert_states:
                alert_state = self.alert_states[alert_key]
                
                if alert_state["state"] == "triggered":
                    # Mark as resolved
                    alert_state["state"] = "resolved"
                    alert_state["resolved_at"] = datetime.utcnow()
                    
                    # Send resolution notification
                    await self._send_resolution_notification(rule, value)
                    
                    logger.info(f"Alert resolved: {rule.name} - {value}")
                    
                    # Clean up state after some time
                    del self.alert_states[alert_key]
        
        except Exception as e:
            logger.error(f"Failed to handle alert resolved: {str(e)}")
    
    async def _send_notifications(self, rule: AlertRule, alert_data: AlertCreate, value: float) -> None:
        """Send notifications for triggered alert"""
        try:
            for channel in rule.notification_channels:
                target = self._get_notification_target(channel)
                if target and target.enabled:
                    await self._send_notification(target, rule, alert_data, value)
        
        except Exception as e:
            logger.error(f"Failed to send notifications: {str(e)}")
    
    async def _send_resolution_notification(self, rule: AlertRule, value: float) -> None:
        """Send notification for resolved alert"""
        try:
            for channel in rule.notification_channels:
                target = self._get_notification_target(channel)
                if target and target.enabled:
                    await self._send_resolution_notification_to_target(target, rule, value)
        
        except Exception as e:
            logger.error(f"Failed to send resolution notification: {str(e)}")
    
    def _get_notification_target(self, channel: NotificationChannel) -> Optional[NotificationTarget]:
        """Get notification target for channel"""
        for target in self.notification_targets:
            if target.channel == channel:
                return target
        return None
    
    async def _send_notification(self, target: NotificationTarget, rule: AlertRule, alert_data: AlertCreate, value: float) -> None:
        """Send notification to specific target"""
        try:
            if target.channel == NotificationChannel.EMAIL:
                await self._send_email_notification(target, rule, alert_data, value)
            elif target.channel == NotificationChannel.SLACK:
                await self._send_slack_notification(target, rule, alert_data, value)
            elif target.channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(target, rule, alert_data, value)
            # Add more notification channels as needed
        
        except Exception as e:
            logger.error(f"Failed to send notification to {target.channel}: {str(e)}")
    
    async def _send_email_notification(self, target: NotificationTarget, rule: AlertRule, alert_data: AlertCreate, value: float) -> None:
        """Send email notification"""
        try:
            config = target.config
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"🚨 OneClass Alert: {rule.name}"
            
            # Create email body
            body = f"""
            <html>
            <body>
                <h2>🚨 OneClass Platform Alert</h2>
                <p><strong>Alert:</strong> {rule.name}</p>
                <p><strong>Severity:</strong> {alert_data.severity.upper()}</p>
                <p><strong>Description:</strong> {alert_data.description}</p>
                <p><strong>Metric:</strong> {alert_data.metric_name}</p>
                <p><strong>Current Value:</strong> {value}</p>
                <p><strong>Threshold:</strong> {alert_data.threshold_value}</p>
                <p><strong>Condition:</strong> {alert_data.condition}</p>
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <hr>
                <p>This alert was generated by the OneClass Platform monitoring system.</p>
                <p>Please investigate and take appropriate action.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                if config['username'] and config['password']:
                    server.login(config['username'], config['password'])
                
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {rule.name}")
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    
    async def _send_slack_notification(self, target: NotificationTarget, rule: AlertRule, alert_data: AlertCreate, value: float) -> None:
        """Send Slack notification"""
        try:
            import httpx
            
            config = target.config
            
            # Determine color based on severity
            color_map = {
                Severity.DEBUG: "#36a64f",     # Green
                Severity.INFO: "#36a64f",      # Green
                Severity.WARNING: "#ff9900",   # Orange
                Severity.ERROR: "#ff0000",     # Red
                Severity.CRITICAL: "#8B0000"   # Dark Red
            }
            
            color = color_map.get(alert_data.severity, "#36a64f")
            
            # Create Slack message
            message = {
                "channel": config['channel'],
                "username": config['username'],
                "icon_emoji": ":rotating_light:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 OneClass Alert: {rule.name}",
                        "text": alert_data.description,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert_data.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Metric",
                                "value": alert_data.metric_name,
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert_data.threshold_value),
                                "short": True
                            }
                        ],
                        "footer": "OneClass Platform Monitoring",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['webhook_url'],
                    json=message,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack alert sent: {rule.name}")
                else:
                    logger.error(f"Failed to send Slack alert: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
    
    async def _send_webhook_notification(self, target: NotificationTarget, rule: AlertRule, alert_data: AlertCreate, value: float) -> None:
        """Send webhook notification"""
        try:
            import httpx
            
            config = target.config
            
            # Create webhook payload
            payload = {
                "alert": {
                    "name": rule.name,
                    "severity": alert_data.severity,
                    "description": alert_data.description,
                    "metric_name": alert_data.metric_name,
                    "current_value": value,
                    "threshold_value": alert_data.threshold_value,
                    "condition": alert_data.condition,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tags": alert_data.tags or {}
                },
                "source": "oneclass-platform",
                "type": "alert_triggered"
            }
            
            # Send webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['webhook_url'],
                    json=payload,
                    headers=config.get('headers', {}),
                    timeout=config.get('timeout', 30)
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook alert sent: {rule.name}")
                else:
                    logger.error(f"Failed to send webhook alert: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
    
    async def _send_resolution_notification_to_target(self, target: NotificationTarget, rule: AlertRule, value: float) -> None:
        """Send resolution notification to specific target"""
        try:
            if target.channel == NotificationChannel.EMAIL:
                await self._send_email_resolution(target, rule, value)
            elif target.channel == NotificationChannel.SLACK:
                await self._send_slack_resolution(target, rule, value)
            elif target.channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_resolution(target, rule, value)
        
        except Exception as e:
            logger.error(f"Failed to send resolution notification: {str(e)}")
    
    async def _send_email_resolution(self, target: NotificationTarget, rule: AlertRule, value: float) -> None:
        """Send email resolution notification"""
        try:
            config = target.config
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"✅ OneClass Alert Resolved: {rule.name}"
            
            # Create email body
            body = f"""
            <html>
            <body>
                <h2>✅ OneClass Platform Alert Resolved</h2>
                <p><strong>Alert:</strong> {rule.name}</p>
                <p><strong>Description:</strong> {rule.description}</p>
                <p><strong>Metric:</strong> {rule.metric_name}</p>
                <p><strong>Current Value:</strong> {value}</p>
                <p><strong>Threshold:</strong> {rule.threshold}</p>
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <hr>
                <p>This alert has been automatically resolved by the OneClass Platform monitoring system.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                if config['username'] and config['password']:
                    server.login(config['username'], config['password'])
                
                server.send_message(msg)
            
            logger.info(f"Email resolution sent: {rule.name}")
        
        except Exception as e:
            logger.error(f"Failed to send email resolution: {str(e)}")
    
    async def _send_slack_resolution(self, target: NotificationTarget, rule: AlertRule, value: float) -> None:
        """Send Slack resolution notification"""
        try:
            import httpx
            
            config = target.config
            
            # Create Slack message
            message = {
                "channel": config['channel'],
                "username": config['username'],
                "icon_emoji": ":white_check_mark:",
                "attachments": [
                    {
                        "color": "#36a64f",  # Green
                        "title": f"✅ OneClass Alert Resolved: {rule.name}",
                        "text": f"Alert has been resolved. Current value: {value}",
                        "fields": [
                            {
                                "title": "Metric",
                                "value": rule.metric_name,
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(value),
                                "short": True
                            }
                        ],
                        "footer": "OneClass Platform Monitoring",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['webhook_url'],
                    json=message,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack resolution sent: {rule.name}")
                else:
                    logger.error(f"Failed to send Slack resolution: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack resolution: {str(e)}")
    
    async def _send_webhook_resolution(self, target: NotificationTarget, rule: AlertRule, value: float) -> None:
        """Send webhook resolution notification"""
        try:
            import httpx
            
            config = target.config
            
            # Create webhook payload
            payload = {
                "alert": {
                    "name": rule.name,
                    "description": rule.description,
                    "metric_name": rule.metric_name,
                    "current_value": value,
                    "threshold_value": rule.threshold,
                    "condition": rule.condition,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "source": "oneclass-platform",
                "type": "alert_resolved"
            }
            
            # Send webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['webhook_url'],
                    json=payload,
                    headers=config.get('headers', {}),
                    timeout=config.get('timeout', 30)
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook resolution sent: {rule.name}")
                else:
                    logger.error(f"Failed to send webhook resolution: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook resolution: {str(e)}")
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule"""
        for i, rule in enumerate(self.alert_rules):
            if rule.name == rule_name:
                del self.alert_rules[i]
                logger.info(f"Removed alert rule: {rule_name}")
                return True
        return False
    
    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return self.alert_rules
    
    def get_alert_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current alert states"""
        return self.alert_states


# Global alerting service instance
alerting_service = AlertingService()