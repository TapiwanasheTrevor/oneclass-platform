# =====================================================
# Paynow Payment Gateway Integration
# File: backend/services/finance/paynow_integration.py
# =====================================================

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import httpx
from fastapi import HTTPException

from .schemas import PaynowPaymentRequest, PaynowPaymentResponse, PaynowStatusResponse

logger = logging.getLogger(__name__)

class PaynowIntegration:
    """Paynow payment gateway integration for Zimbabwe"""
    
    def __init__(self, integration_id: str, integration_key: str, 
                 return_url: str, result_url: str):
        self.integration_id = integration_id
        self.integration_key = integration_key
        self.return_url = return_url
        self.result_url = result_url
        self.base_url = "https://www.paynow.co.zw"
        
    def _generate_hash(self, values: Dict[str, Any]) -> str:
        """Generate hash for Paynow request"""
        # Sort values by key
        sorted_values = sorted(values.items())
        
        # Create string to hash
        string_to_hash = ""
        for key, value in sorted_values:
            string_to_hash += f"{key}={value}&"
        
        # Remove trailing &
        string_to_hash = string_to_hash.rstrip('&')
        
        # Add integration key
        string_to_hash += self.integration_key
        
        # Generate SHA512 hash
        return hashlib.sha512(string_to_hash.encode()).hexdigest().upper()
    
    def _verify_hash(self, values: Dict[str, Any], received_hash: str) -> bool:
        """Verify hash from Paynow response"""
        # Remove hash from values for verification
        values_copy = values.copy()
        values_copy.pop('hash', None)
        
        generated_hash = self._generate_hash(values_copy)
        return generated_hash == received_hash.upper()
    
    async def initiate_payment(self, payment_request: PaynowPaymentRequest, 
                              payment_reference: str) -> PaynowPaymentResponse:
        """Initiate payment with Paynow"""
        try:
            # Prepare payment data
            payment_data = {
                'id': self.integration_id,
                'reference': payment_reference,
                'amount': str(payment_request.amount),
                'additionalinfo': f"Payment for student {payment_request.student_id}",
                'returnurl': self.return_url,
                'resulturl': self.result_url,
                'authemail': payment_request.payer_email,
                'phone': payment_request.payer_phone,
                'method': 'express'  # Express checkout
            }
            
            # Generate hash
            payment_data['hash'] = self._generate_hash(payment_data)
            
            # Make request to Paynow
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/interface/initiatetransaction",
                    data=payment_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Paynow request failed with status {response.status_code}: {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail="Payment gateway request failed"
                    )
                
                # Parse response
                response_data = {}
                for line in response.text.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key.lower()] = value
                
                # Verify hash
                received_hash = response_data.get('hash', '')
                if not self._verify_hash(response_data, received_hash):
                    logger.error("Invalid hash in Paynow response")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid payment gateway response"
                    )
                
                # Check if request was successful
                status = response_data.get('status', '').lower()
                if status != 'ok':
                    error_message = response_data.get('error', 'Unknown error')
                    logger.error(f"Paynow payment initiation failed: {error_message}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Payment initiation failed: {error_message}"
                    )
                
                # Extract response data
                paynow_reference = response_data.get('paynowreference', '')
                poll_url = response_data.get('pollurl', '')
                browser_url = response_data.get('browserurl', '')
                
                if not all([paynow_reference, poll_url, browser_url]):
                    logger.error("Missing required fields in Paynow response")
                    raise HTTPException(
                        status_code=500,
                        detail="Incomplete payment gateway response"
                    )
                
                logger.info(f"Payment initiated successfully: {paynow_reference}")
                
                return PaynowPaymentResponse(
                    payment_id=UUID(str(payment_request.student_id)),  # Will be replaced with actual payment ID
                    paynow_reference=paynow_reference,
                    poll_url=poll_url,
                    redirect_url=browser_url,
                    status=status,
                    success=True,
                    hash_valid=True
                )
                
        except httpx.RequestError as e:
            logger.error(f"Network error during Paynow request: {e}")
            raise HTTPException(
                status_code=503,
                detail="Payment gateway temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {e}")
            raise HTTPException(
                status_code=500,
                detail="Payment initiation failed"
            )
    
    async def check_payment_status(self, poll_url: str) -> PaynowStatusResponse:
        """Check payment status using poll URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(poll_url)
                
                if response.status_code != 200:
                    logger.error(f"Paynow status check failed with status {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Payment status check failed"
                    )
                
                # Parse response
                response_data = {}
                for line in response.text.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key.lower()] = value
                
                # Verify hash
                received_hash = response_data.get('hash', '')
                hash_valid = self._verify_hash(response_data, received_hash)
                
                if not hash_valid:
                    logger.warning("Invalid hash in Paynow status response")
                
                # Extract payment information
                paynow_reference = response_data.get('paynowreference', '')
                status = response_data.get('status', '').lower()
                amount = Decimal(response_data.get('amount', '0.00'))
                
                # Map Paynow status to our status
                payment_status = self._map_paynow_status(status)
                
                return PaynowStatusResponse(
                    payment_id=UUID('00000000-0000-0000-0000-000000000000'),  # Will be replaced
                    status=payment_status,
                    paynow_reference=paynow_reference,
                    amount=amount,
                    success=status == 'paid',
                    hash_valid=hash_valid,
                    message=response_data.get('pollmessage', '')
                )
                
        except httpx.RequestError as e:
            logger.error(f"Network error during status check: {e}")
            raise HTTPException(
                status_code=503,
                detail="Payment status check temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error during status check: {e}")
            raise HTTPException(
                status_code=500,
                detail="Payment status check failed"
            )
    
    def _map_paynow_status(self, paynow_status: str) -> str:
        """Map Paynow status to our payment status enum"""
        status_mapping = {
            'paid': 'completed',
            'awaiting delivery': 'processing',
            'delivered': 'completed',
            'cancelled': 'cancelled',
            'disputed': 'failed',
            'refunded': 'refunded',
            'pending': 'pending',
            'sent': 'processing',
            'created': 'pending'
        }
        
        return status_mapping.get(paynow_status.lower(), 'pending')
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook notification from Paynow"""
        try:
            # Verify hash
            received_hash = webhook_data.get('hash', '')
            hash_valid = self._verify_hash(webhook_data, received_hash)
            
            if not hash_valid:
                logger.error("Invalid hash in webhook data")
                return {
                    'success': False,
                    'error': 'Invalid hash',
                    'hash_valid': False
                }
            
            # Extract payment information
            paynow_reference = webhook_data.get('paynowreference', '')
            reference = webhook_data.get('reference', '')
            status = webhook_data.get('status', '').lower()
            amount = Decimal(webhook_data.get('amount', '0.00'))
            
            # Map status
            payment_status = self._map_paynow_status(status)
            
            logger.info(f"Webhook received for payment {reference}: {status}")
            
            return {
                'success': True,
                'paynow_reference': paynow_reference,
                'reference': reference,
                'status': payment_status,
                'amount': amount,
                'hash_valid': hash_valid,
                'raw_data': webhook_data
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {
                'success': False,
                'error': str(e),
                'hash_valid': False
            }
    
    async def initiate_mobile_payment(self, payment_request: PaynowPaymentRequest,
                                    payment_reference: str, method: str = 'ecocash') -> PaynowPaymentResponse:
        """Initiate mobile money payment (EcoCash, OneMoney)"""
        try:
            # Prepare payment data for mobile money
            payment_data = {
                'id': self.integration_id,
                'reference': payment_reference,
                'amount': str(payment_request.amount),
                'additionalinfo': f"Payment for student {payment_request.student_id}",
                'returnurl': self.return_url,
                'resulturl': self.result_url,
                'authemail': payment_request.payer_email,
                'phone': payment_request.payer_phone,
                'method': method  # 'ecocash' or 'onemoney'
            }
            
            # Generate hash
            payment_data['hash'] = self._generate_hash(payment_data)
            
            # Make request to Paynow
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/interface/remotetransaction",
                    data=payment_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Mobile payment request failed with status {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Mobile payment request failed"
                    )
                
                # Parse response
                response_data = {}
                for line in response.text.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key.lower()] = value
                
                # Verify hash
                received_hash = response_data.get('hash', '')
                if not self._verify_hash(response_data, received_hash):
                    logger.error("Invalid hash in mobile payment response")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid payment gateway response"
                    )
                
                # Check if request was successful
                status = response_data.get('status', '').lower()
                if status != 'ok':
                    error_message = response_data.get('error', 'Unknown error')
                    logger.error(f"Mobile payment initiation failed: {error_message}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Mobile payment failed: {error_message}"
                    )
                
                # Extract response data
                paynow_reference = response_data.get('paynowreference', '')
                poll_url = response_data.get('pollurl', '')
                instructions = response_data.get('instructions', '')
                
                logger.info(f"Mobile payment initiated: {paynow_reference}")
                
                return PaynowPaymentResponse(
                    payment_id=UUID(str(payment_request.student_id)),  # Will be replaced
                    paynow_reference=paynow_reference,
                    poll_url=poll_url,
                    redirect_url=instructions,  # Instructions for mobile payment
                    status=status,
                    success=True,
                    hash_valid=True
                )
                
        except httpx.RequestError as e:
            logger.error(f"Network error during mobile payment: {e}")
            raise HTTPException(
                status_code=503,
                detail="Mobile payment service temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error during mobile payment: {e}")
            raise HTTPException(
                status_code=500,
                detail="Mobile payment initiation failed"
            )

# Factory function to create PaynowIntegration from school config
def create_paynow_integration(school_config: Dict[str, Any]) -> PaynowIntegration:
    """Create PaynowIntegration instance from school configuration"""
    paynow_config = school_config.get('paynow_config', {})
    
    if not paynow_config:
        raise HTTPException(
            status_code=400,
            detail="Paynow not configured for this school"
        )
    
    required_fields = ['integration_id', 'integration_key', 'return_url', 'result_url']
    for field in required_fields:
        if field not in paynow_config:
            raise HTTPException(
                status_code=400,
                detail=f"Paynow configuration missing: {field}"
            )
    
    return PaynowIntegration(
        integration_id=paynow_config['integration_id'],
        integration_key=paynow_config['integration_key'],
        return_url=paynow_config['return_url'],
        result_url=paynow_config['result_url']
    )

# Utility functions for payment processing
def validate_zimbabwe_phone(phone: str) -> bool:
    """Validate Zimbabwe phone number format"""
    import re
    pattern = r'^(\+263|0)[0-9]{9}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

def format_zimbabwe_phone(phone: str) -> str:
    """Format Zimbabwe phone number for Paynow"""
    # Remove spaces and dashes
    clean_phone = phone.replace(' ', '').replace('-', '')
    
    # Convert to international format
    if clean_phone.startswith('0'):
        clean_phone = '+263' + clean_phone[1:]
    elif not clean_phone.startswith('+263'):
        clean_phone = '+263' + clean_phone
    
    return clean_phone

def is_mobile_money_available(amount: Decimal) -> bool:
    """Check if mobile money is available for the amount"""
    # Mobile money limits in Zimbabwe (these may change)
    max_daily_limit = Decimal('1000.00')  # USD
    max_transaction_limit = Decimal('500.00')  # USD
    
    return amount <= max_transaction_limit

def get_payment_method_fees(method: str, amount: Decimal) -> Decimal:
    """Calculate payment method fees"""
    # These are approximate fees and should be updated with actual rates
    fee_structures = {
        'ecocash': {
            'percentage': Decimal('0.015'),  # 1.5%
            'minimum': Decimal('0.05'),
            'maximum': Decimal('5.00')
        },
        'onemoney': {
            'percentage': Decimal('0.015'),  # 1.5%
            'minimum': Decimal('0.05'),
            'maximum': Decimal('5.00')
        },
        'card': {
            'percentage': Decimal('0.035'),  # 3.5%
            'minimum': Decimal('0.10'),
            'maximum': Decimal('10.00')
        }
    }
    
    if method not in fee_structures:
        return Decimal('0.00')
    
    fee_config = fee_structures[method]
    calculated_fee = amount * fee_config['percentage']
    
    # Apply minimum and maximum limits
    final_fee = max(fee_config['minimum'], calculated_fee)
    final_fee = min(fee_config['maximum'], final_fee)
    
    return final_fee