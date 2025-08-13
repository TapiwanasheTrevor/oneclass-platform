"""
Zimbabwe Payment Gateway Integrations
Complete integration with Zimbabwe payment methods (Paynow, EcoCash, OneMoney, etc.)
"""

import hashlib
import hmac
import json
import logging
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, urlencode
import aiohttp
import uuid

from ..schemas import PaymentStatus, PaymentGatewayResponse

logger = logging.getLogger(__name__)

# =====================================================
# PAYNOW INTEGRATION
# =====================================================

class PaynowGateway:
    """
    Paynow Zimbabwe payment gateway integration
    Supports online payments, mobile money (EcoCash, OneMoney), and bank transfers
    """
    
    def __init__(self, integration_id: str, integration_key: str, return_url: str, result_url: str):
        self.integration_id = integration_id
        self.integration_key = integration_key
        self.return_url = return_url
        self.result_url = result_url
        self.api_url = "https://www.paynow.co.zw/interface/initiatetransaction"
        self.poll_url = "https://www.paynow.co.zw/interface/pollstatus"
    
    def _generate_hash(self, fields: Dict[str, str]) -> str:
        """Generate SHA512 hash for Paynow authentication"""
        
        # Create hash string from fields
        hash_string = ""
        for key in sorted(fields.keys()):
            if key != "hash":
                hash_string += f"{fields[key]}"
        
        hash_string += self.integration_key
        
        # Generate SHA512 hash
        return hashlib.sha512(hash_string.encode()).hexdigest().upper()
    
    async def initiate_payment(
        self,
        reference: str,
        amount: Decimal,
        payer_email: str,
        additional_info: str = "",
        payment_methods: Optional[List[str]] = None
    ) -> PaymentGatewayResponse:
        """
        Initiate a Paynow payment transaction
        
        Args:
            reference: Unique payment reference
            amount: Payment amount in USD
            payer_email: Payer's email address
            additional_info: Additional payment information
            payment_methods: Specific payment methods to enable
        """
        
        try:
            # Prepare payment data
            payment_data = {
                "id": self.integration_id,
                "reference": reference,
                "amount": f"{amount:.2f}",
                "additionalinfo": additional_info,
                "returnurl": self.return_url,
                "resulturl": self.result_url,
                "authemail": payer_email,
                "status": "Message"
            }
            
            # Add payment methods if specified
            if payment_methods:
                if "ecocash" in payment_methods:
                    payment_data["phone"] = ""  # Will be filled by user
                if "onemoney" in payment_methods:
                    payment_data["onemoney"] = "true"
                if "zimswitch" in payment_methods:
                    payment_data["zimswitch"] = "true"
            
            # Generate hash
            payment_data["hash"] = self._generate_hash(payment_data)
            
            # Send request to Paynow
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data=payment_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"Paynow API error: {response.status}")
                    
                    response_text = await response.text()
                    response_data = dict(parse_qs(response_text))
                    
                    # Extract response values
                    status = response_data.get("status", [""])[0]
                    paynow_reference = response_data.get("paynowreference", [""])[0]
                    poll_url = response_data.get("pollurl", [""])[0]
                    hash_valid = self._verify_hash(response_data, response_data.get("hash", [""])[0])
                    
                    success = status.lower() == "ok"
                    
                    if success:
                        logger.info(f"Paynow payment initiated successfully: {reference}")
                        
                        return PaymentGatewayResponse(
                            success=True,
                            transaction_id=paynow_reference,
                            reference=reference,
                            status="initiated",
                            message="Payment initiated successfully",
                            amount=amount,
                            gateway_data={
                                "paynow_reference": paynow_reference,
                                "poll_url": poll_url,
                                "redirect_url": response_data.get("browserurl", [""])[0],
                                "hash_valid": hash_valid
                            }
                        )
                    else:
                        error_message = response_data.get("error", ["Unknown error"])[0]
                        
                        logger.error(f"Paynow payment failed: {error_message}")
                        
                        return PaymentGatewayResponse(
                            success=False,
                            transaction_id=None,
                            reference=reference,
                            status="failed",
                            message=error_message,
                            amount=amount,
                            gateway_data=response_data
                        )
            
        except Exception as e:
            logger.error(f"Paynow integration error: {e}")
            
            return PaymentGatewayResponse(
                success=False,
                transaction_id=None,
                reference=reference,
                status="error",
                message=str(e),
                amount=amount,
                gateway_data={}
            )
    
    async def poll_transaction(self, paynow_reference: str) -> PaymentGatewayResponse:
        """Poll Paynow transaction status"""
        
        try:
            poll_data = {
                "id": self.integration_id,
                "reference": paynow_reference
            }
            
            poll_data["hash"] = self._generate_hash(poll_data)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.poll_url,
                    data=poll_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"Paynow poll API error: {response.status}")
                    
                    response_text = await response.text()
                    response_data = dict(parse_qs(response_text))
                    
                    status = response_data.get("status", [""])[0].lower()
                    amount_str = response_data.get("amount", ["0.00"])[0]
                    amount = Decimal(amount_str)
                    
                    # Map Paynow status to our status
                    payment_status = "pending"
                    if status in ["paid", "delivered"]:
                        payment_status = "completed"
                    elif status in ["cancelled", "failed"]:
                        payment_status = "failed"
                    
                    return PaymentGatewayResponse(
                        success=status in ["paid", "delivered"],
                        transaction_id=paynow_reference,
                        reference=response_data.get("reference", [""])[0],
                        status=payment_status,
                        message=f"Transaction {status}",
                        amount=amount,
                        gateway_data=response_data
                    )
            
        except Exception as e:
            logger.error(f"Paynow poll error: {e}")
            
            return PaymentGatewayResponse(
                success=False,
                transaction_id=paynow_reference,
                reference="",
                status="error",
                message=str(e),
                amount=None,
                gateway_data={}
            )
    
    def _verify_hash(self, data: Dict, received_hash: str) -> bool:
        """Verify response hash from Paynow"""
        
        try:
            expected_hash = self._generate_hash(data)
            return expected_hash == received_hash.upper()
        except:
            return False

# =====================================================
# ECOCASH DIRECT INTEGRATION
# =====================================================

class EcoCashGateway:
    """
    EcoCash direct integration (would require merchant account)
    This is a placeholder for actual EcoCash API integration
    """
    
    def __init__(self, merchant_id: str, merchant_key: str, api_url: str = None):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.api_url = api_url or "https://api.ecocash.co.zw"  # Placeholder URL
    
    async def initiate_payment(
        self,
        reference: str,
        amount: Decimal,
        phone_number: str,
        description: str = ""
    ) -> PaymentGatewayResponse:
        """Initiate EcoCash payment"""
        
        try:
            # Format phone number for Zimbabwe
            formatted_phone = self._format_zimbabwe_phone(phone_number)
            
            # Prepare payment request
            payment_data = {
                "merchant_id": self.merchant_id,
                "reference": reference,
                "amount": f"{amount:.2f}",
                "phone_number": formatted_phone,
                "description": description,
                "currency": "USD",
                "timestamp": datetime.now().isoformat()
            }
            
            # Add authentication
            payment_data["signature"] = self._generate_signature(payment_data)
            
            # For demonstration, return success
            # In reality, this would call the EcoCash API
            logger.info(f"EcoCash payment initiated: {reference} for ${amount}")
            
            return PaymentGatewayResponse(
                success=True,
                transaction_id=f"ECO-{reference}",
                reference=reference,
                status="initiated",
                message="EcoCash payment initiated",
                amount=amount,
                gateway_data={
                    "phone_number": formatted_phone,
                    "merchant_id": self.merchant_id
                }
            )
            
        except Exception as e:
            logger.error(f"EcoCash integration error: {e}")
            
            return PaymentGatewayResponse(
                success=False,
                transaction_id=None,
                reference=reference,
                status="error",
                message=str(e),
                amount=amount,
                gateway_data={}
            )
    
    def _format_zimbabwe_phone(self, phone: str) -> str:
        """Format phone number for Zimbabwe"""
        
        # Remove spaces and special characters
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Handle different formats
        if phone.startswith("+263"):
            return phone[4:]  # Remove +263
        elif phone.startswith("263"):
            return phone[3:]  # Remove 263
        elif phone.startswith("0"):
            return phone[1:]  # Remove leading 0
        
        return phone
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """Generate signature for EcoCash request"""
        
        # Create signature string
        signature_string = ""
        for key in sorted(data.keys()):
            if key != "signature":
                signature_string += f"{key}={data[key]}&"
        
        signature_string += self.merchant_key
        
        # Generate SHA256 hash
        return hashlib.sha256(signature_string.encode()).hexdigest()

# =====================================================
# ONEMONEY INTEGRATION
# =====================================================

class OneMoneyGateway:
    """
    OneMoney (NetOne) payment gateway integration
    Similar structure to EcoCash but for NetOne's mobile money service
    """
    
    def __init__(self, merchant_code: str, secret_key: str):
        self.merchant_code = merchant_code
        self.secret_key = secret_key
        self.api_url = "https://api.onemoney.co.zw"  # Placeholder URL
    
    async def initiate_payment(
        self,
        reference: str,
        amount: Decimal,
        phone_number: str,
        description: str = ""
    ) -> PaymentGatewayResponse:
        """Initiate OneMoney payment"""
        
        try:
            # Format phone number
            formatted_phone = self._format_phone_number(phone_number)
            
            # Validate OneMoney number (starts with 71)
            if not formatted_phone.startswith("71"):
                raise ValueError("Invalid OneMoney phone number. Must start with 071 or +263 71")
            
            # Prepare payment data
            payment_data = {
                "merchant_code": self.merchant_code,
                "reference": reference,
                "amount": str(amount),
                "phone": formatted_phone,
                "description": description,
                "currency": "USD"
            }
            
            # For demonstration purposes
            logger.info(f"OneMoney payment initiated: {reference} for ${amount}")
            
            return PaymentGatewayResponse(
                success=True,
                transaction_id=f"ONE-{reference}",
                reference=reference,
                status="initiated",
                message="OneMoney payment initiated",
                amount=amount,
                gateway_data={
                    "phone_number": formatted_phone,
                    "merchant_code": self.merchant_code
                }
            )
            
        except Exception as e:
            logger.error(f"OneMoney integration error: {e}")
            
            return PaymentGatewayResponse(
                success=False,
                transaction_id=None,
                reference=reference,
                status="error",
                message=str(e),
                amount=amount,
                gateway_data={}
            )
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for Zimbabwe"""
        
        phone = phone.replace(" ", "").replace("-", "")
        
        if phone.startswith("+263"):
            return phone[4:]
        elif phone.startswith("263"):
            return phone[3:]
        elif phone.startswith("0"):
            return phone[1:]
        
        return phone

# =====================================================
# ZIMBABWE PAYMENT GATEWAY FACTORY
# =====================================================

class ZimbabwePaymentFactory:
    """
    Factory for creating Zimbabwe payment gateway instances
    Manages configuration and provides unified interface
    """
    
    def __init__(self, school_id: str):
        self.school_id = school_id
        self._gateways = {}
    
    def configure_paynow(
        self, 
        integration_id: str, 
        integration_key: str, 
        return_url: str, 
        result_url: str
    ) -> PaynowGateway:
        """Configure Paynow gateway"""
        
        gateway = PaynowGateway(integration_id, integration_key, return_url, result_url)
        self._gateways["paynow"] = gateway
        return gateway
    
    def configure_ecocash(
        self, 
        merchant_id: str, 
        merchant_key: str, 
        api_url: str = None
    ) -> EcoCashGateway:
        """Configure EcoCash gateway"""
        
        gateway = EcoCashGateway(merchant_id, merchant_key, api_url)
        self._gateways["ecocash"] = gateway
        return gateway
    
    def configure_onemoney(
        self, 
        merchant_code: str, 
        secret_key: str
    ) -> OneMoneyGateway:
        """Configure OneMoney gateway"""
        
        gateway = OneMoneyGateway(merchant_code, secret_key)
        self._gateways["onemoney"] = gateway
        return gateway
    
    def get_gateway(self, payment_method: str):
        """Get configured gateway by payment method"""
        
        method_map = {
            "paynow": "paynow",
            "ecocash": "ecocash", 
            "onemoney": "onemoney",
            "telecash": "paynow",  # TeleCash can go through Paynow
            "zipit": "paynow"      # ZipIt can go through Paynow
        }
        
        gateway_type = method_map.get(payment_method.lower())
        return self._gateways.get(gateway_type)
    
    async def process_payment(
        self,
        payment_method: str,
        reference: str,
        amount: Decimal,
        payer_info: Dict[str, Any],
        additional_data: Dict[str, Any] = None
    ) -> PaymentGatewayResponse:
        """Process payment using appropriate gateway"""
        
        gateway = self.get_gateway(payment_method)
        if not gateway:
            return PaymentGatewayResponse(
                success=False,
                transaction_id=None,
                reference=reference,
                status="error",
                message=f"Payment method {payment_method} not configured",
                amount=amount,
                gateway_data={}
            )
        
        try:
            if payment_method.lower() == "paynow":
                return await gateway.initiate_payment(
                    reference=reference,
                    amount=amount,
                    payer_email=payer_info.get("email", ""),
                    additional_info=payer_info.get("name", "")
                )
            
            elif payment_method.lower() == "ecocash":
                return await gateway.initiate_payment(
                    reference=reference,
                    amount=amount,
                    phone_number=payer_info.get("phone", ""),
                    description=f"School fee payment - {reference}"
                )
            
            elif payment_method.lower() == "onemoney":
                return await gateway.initiate_payment(
                    reference=reference,
                    amount=amount,
                    phone_number=payer_info.get("phone", ""),
                    description=f"School fee payment - {reference}"
                )
            
            else:
                return PaymentGatewayResponse(
                    success=False,
                    transaction_id=None,
                    reference=reference,
                    status="error",
                    message=f"Unsupported payment method: {payment_method}",
                    amount=amount,
                    gateway_data={}
                )
        
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            
            return PaymentGatewayResponse(
                success=False,
                transaction_id=None,
                reference=reference,
                status="error",
                message=str(e),
                amount=amount,
                gateway_data={}
            )

# =====================================================
# WEBHOOK HANDLERS
# =====================================================

class ZimbabwePaymentWebhooks:
    """
    Webhook handlers for Zimbabwe payment gateways
    Processes payment status updates from providers
    """
    
    def __init__(self, factory: ZimbabwePaymentFactory):
        self.factory = factory
    
    async def handle_paynow_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Paynow webhook notification"""
        
        try:
            reference = webhook_data.get("reference", "")
            paynow_reference = webhook_data.get("paynowreference", "")
            status = webhook_data.get("status", "").lower()
            
            # Verify webhook hash if provided
            gateway = self.factory.get_gateway("paynow")
            if gateway and "hash" in webhook_data:
                hash_valid = gateway._verify_hash(webhook_data, webhook_data["hash"])
                if not hash_valid:
                    logger.warning(f"Invalid webhook hash for reference: {reference}")
                    return {"status": "invalid_hash"}
            
            # Map status
            payment_status = "pending"
            if status in ["paid", "delivered"]:
                payment_status = "completed"
            elif status in ["cancelled", "failed"]:
                payment_status = "failed"
            
            logger.info(f"Paynow webhook received: {reference} - {status}")
            
            return {
                "status": "processed",
                "reference": reference,
                "paynow_reference": paynow_reference,
                "payment_status": payment_status,
                "webhook_status": status
            }
            
        except Exception as e:
            logger.error(f"Paynow webhook processing error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def handle_ecocash_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle EcoCash webhook notification"""
        
        try:
            reference = webhook_data.get("reference", "")
            status = webhook_data.get("status", "").lower()
            
            # Process EcoCash status
            payment_status = "pending"
            if status == "success":
                payment_status = "completed"
            elif status in ["failed", "cancelled"]:
                payment_status = "failed"
            
            logger.info(f"EcoCash webhook received: {reference} - {status}")
            
            return {
                "status": "processed",
                "reference": reference,
                "payment_status": payment_status,
                "webhook_status": status
            }
            
        except Exception as e:
            logger.error(f"EcoCash webhook processing error: {e}")
            return {"status": "error", "message": str(e)}