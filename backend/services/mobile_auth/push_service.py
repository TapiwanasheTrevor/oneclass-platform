"""
Push Notification Service
Handles Firebase Cloud Messaging (FCM) and Apple Push Notification Service (APNS)
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from pydantic import BaseModel

from shared.config import settings
from shared.exceptions import ExternalServiceError
from .models import DeviceRegistration, MobilePushNotification

logger = logging.getLogger(__name__)


class PushMessage(BaseModel):
    """Push notification message structure"""
    title: str
    body: str
    data: Dict[str, Any] = {}
    priority: str = "normal"  # normal, high
    badge: Optional[int] = None
    sound: Optional[str] = None
    click_action: Optional[str] = None
    image_url: Optional[str] = None


class FCMService:
    """Firebase Cloud Messaging service"""
    
    def __init__(self, server_key: str):
        self.server_key = server_key
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.headers = {
            "Authorization": f"key={server_key}",
            "Content-Type": "application/json"
        }
    
    async def send_to_device(self, device_token: str, message: PushMessage) -> Dict[str, Any]:
        """Send push notification to a single device"""
        payload = {
            "to": device_token,
            "notification": {
                "title": message.title,
                "body": message.body,
                "sound": message.sound or "default",
                "click_action": message.click_action,
                "image": message.image_url
            },
            "data": message.data,
            "priority": message.priority
        }
        
        if message.badge is not None:
            payload["notification"]["badge"] = message.badge
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success") == 1:
                        return {
                            "success": True,
                            "message_id": result.get("results", [{}])[0].get("message_id"),
                            "canonical_id": result.get("canonical_ids")
                        }
                    else:
                        error = result.get("results", [{}])[0].get("error")
                        return {
                            "success": False,
                            "error": error,
                            "details": result
                        }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
        
        except Exception as e:
            logger.error(f"FCM send error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_to_multiple_devices(self, device_tokens: List[str], message: PushMessage) -> Dict[str, Any]:
        """Send push notification to multiple devices"""
        payload = {
            "registration_ids": device_tokens,
            "notification": {
                "title": message.title,
                "body": message.body,
                "sound": message.sound or "default",
                "click_action": message.click_action,
                "image": message.image_url
            },
            "data": message.data,
            "priority": message.priority
        }
        
        if message.badge is not None:
            payload["notification"]["badge"] = message.badge
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "success": True,
                        "success_count": result.get("success", 0),
                        "failure_count": result.get("failure", 0),
                        "results": result.get("results", [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
        
        except Exception as e:
            logger.error(f"FCM multicast send error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_to_topic(self, topic: str, message: PushMessage) -> Dict[str, Any]:
        """Send push notification to a topic"""
        payload = {
            "to": f"/topics/{topic}",
            "notification": {
                "title": message.title,
                "body": message.body,
                "sound": message.sound or "default",
                "click_action": message.click_action,
                "image": message.image_url
            },
            "data": message.data,
            "priority": message.priority
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "success": True,
                        "message_id": result.get("message_id")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
        
        except Exception as e:
            logger.error(f"FCM topic send error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class APNSService:
    """Apple Push Notification Service"""
    
    def __init__(self, key_id: str, team_id: str, bundle_id: str, key_path: str):
        self.key_id = key_id
        self.team_id = team_id
        self.bundle_id = bundle_id
        self.key_path = key_path
        self.apns_url = "https://api.push.apple.com/3/device"
        
        # For production, use: https://api.push.apple.com/3/device
        # For sandbox, use: https://api.sandbox.push.apple.com/3/device
    
    async def send_to_device(self, device_token: str, message: PushMessage) -> Dict[str, Any]:
        """Send push notification to iOS device"""
        # Create JWT token for authentication
        jwt_token = self._create_jwt_token()
        
        # Create APNS payload
        payload = {
            "aps": {
                "alert": {
                    "title": message.title,
                    "body": message.body
                },
                "sound": message.sound or "default"
            }
        }
        
        if message.badge is not None:
            payload["aps"]["badge"] = message.badge
        
        # Add custom data
        if message.data:
            payload.update(message.data)
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "apns-topic": self.bundle_id,
            "apns-priority": "10" if message.priority == "high" else "5",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.apns_url}/{device_token}",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message_id": response.headers.get("apns-id")
                    }
                else:
                    error_data = response.json() if response.content else {}
                    return {
                        "success": False,
                        "error": error_data.get("reason", f"HTTP {response.status_code}"),
                        "details": error_data
                    }
        
        except Exception as e:
            logger.error(f"APNS send error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_jwt_token(self) -> str:
        """Create JWT token for APNS authentication"""
        # This would create a proper JWT token using the APNS private key
        # For now, we'll return a placeholder
        import jwt
        from datetime import datetime, timedelta
        
        # Load private key
        try:
            with open(self.key_path, 'rb') as key_file:
                private_key = key_file.read()
        except FileNotFoundError:
            logger.error(f"APNS private key not found: {self.key_path}")
            raise ExternalServiceError("APNS private key not found")
        
        # Create JWT payload
        payload = {
            "iss": self.team_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Create JWT token
        token = jwt.encode(
            payload,
            private_key,
            algorithm="ES256",
            headers={"kid": self.key_id}
        )
        
        return token


class PushNotificationService:
    """Main push notification service"""
    
    def __init__(self):
        self.fcm_service = None
        self.apns_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize push notification services"""
        # Initialize FCM
        if hasattr(settings, 'FCM_SERVER_KEY') and settings.FCM_SERVER_KEY:
            self.fcm_service = FCMService(settings.FCM_SERVER_KEY)
        
        # Initialize APNS
        if (hasattr(settings, 'APNS_KEY_ID') and settings.APNS_KEY_ID and
            hasattr(settings, 'APNS_TEAM_ID') and settings.APNS_TEAM_ID and
            hasattr(settings, 'APNS_BUNDLE_ID') and settings.APNS_BUNDLE_ID and
            hasattr(settings, 'APNS_KEY_PATH') and settings.APNS_KEY_PATH):
            
            self.apns_service = APNSService(
                settings.APNS_KEY_ID,
                settings.APNS_TEAM_ID,
                settings.APNS_BUNDLE_ID,
                settings.APNS_KEY_PATH
            )
    
    async def send_to_device(self, device: DeviceRegistration, message: PushMessage) -> Dict[str, Any]:
        """Send push notification to a specific device"""
        if device.device_type == "android" and device.fcm_token and self.fcm_service:
            return await self.fcm_service.send_to_device(device.fcm_token, message)
        elif device.device_type == "ios" and device.apns_token and self.apns_service:
            return await self.apns_service.send_to_device(device.apns_token, message)
        else:
            return {
                "success": False,
                "error": "No valid push token or service not configured"
            }
    
    async def send_to_devices(self, devices: List[DeviceRegistration], message: PushMessage) -> Dict[str, Any]:
        """Send push notification to multiple devices"""
        results = []
        
        # Group devices by platform
        android_tokens = []
        ios_tokens = []
        
        for device in devices:
            if device.device_type == "android" and device.fcm_token:
                android_tokens.append(device.fcm_token)
            elif device.device_type == "ios" and device.apns_token:
                ios_tokens.append(device.apns_token)
        
        # Send to Android devices
        if android_tokens and self.fcm_service:
            if len(android_tokens) == 1:
                result = await self.fcm_service.send_to_device(android_tokens[0], message)
                results.append({"platform": "android", "result": result})
            else:
                result = await self.fcm_service.send_to_multiple_devices(android_tokens, message)
                results.append({"platform": "android", "result": result})
        
        # Send to iOS devices
        if ios_tokens and self.apns_service:
            for token in ios_tokens:
                result = await self.apns_service.send_to_device(token, message)
                results.append({"platform": "ios", "result": result})
        
        # Calculate totals
        total_success = sum(1 for r in results if r["result"].get("success"))
        total_failure = len(results) - total_success
        
        return {
            "success": total_success > 0,
            "total_sent": len(results),
            "success_count": total_success,
            "failure_count": total_failure,
            "results": results
        }
    
    async def send_to_topic(self, topic: str, message: PushMessage, platforms: List[str] = None) -> Dict[str, Any]:
        """Send push notification to a topic"""
        if platforms is None:
            platforms = ["android", "ios"]
        
        results = []
        
        # Send to Android topic
        if "android" in platforms and self.fcm_service:
            result = await self.fcm_service.send_to_topic(f"android_{topic}", message)
            results.append({"platform": "android", "result": result})
        
        # Send to iOS topic
        if "ios" in platforms and self.apns_service:
            # iOS topics are handled differently in APNS
            # For now, we'll skip topic-based notifications for iOS
            pass
        
        return {
            "success": len(results) > 0,
            "results": results
        }
    
    async def send_notification(self, notification: MobilePushNotification, device: DeviceRegistration) -> Dict[str, Any]:
        """Send a stored notification to a device"""
        message = PushMessage(
            title=notification.title,
            body=notification.body,
            data=notification.data,
            priority=notification.priority
        )
        
        result = await self.send_to_device(device, message)
        
        # Update notification status
        if result.get("success"):
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
        else:
            notification.status = "failed"
            notification.error_message = result.get("error")
            notification.retry_count += 1
        
        return result
    
    def create_notification_message(self, notification_type: str, data: Dict[str, Any]) -> PushMessage:
        """Create a push message based on notification type"""
        if notification_type == "grade":
            return PushMessage(
                title="New Grade Posted",
                body=f"You have a new grade in {data.get('subject', 'a subject')}",
                data={"type": "grade", "subject_id": data.get("subject_id")},
                priority="high"
            )
        elif notification_type == "attendance":
            return PushMessage(
                title="Attendance Update",
                body=f"Your attendance has been updated for {data.get('subject', 'a class')}",
                data={"type": "attendance", "class_id": data.get("class_id")},
                priority="normal"
            )
        elif notification_type == "payment":
            return PushMessage(
                title="Payment Reminder",
                body=f"Payment due: {data.get('amount', 'Amount')} for {data.get('item', 'school fees')}",
                data={"type": "payment", "payment_id": data.get("payment_id")},
                priority="high"
            )
        elif notification_type == "announcement":
            return PushMessage(
                title="School Announcement",
                body=data.get("message", "New announcement from school"),
                data={"type": "announcement", "announcement_id": data.get("announcement_id")},
                priority="normal"
            )
        else:
            return PushMessage(
                title="Notification",
                body=data.get("message", "You have a new notification"),
                data={"type": notification_type},
                priority="normal"
            )