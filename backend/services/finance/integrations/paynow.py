# =====================================================
# Paynow Payment Gateway Integration
# File: backend/services/finance/integrations/paynow.py
# =====================================================

import hashlib
import hmac
import urllib.parse
from typing import Dict, Optional, Any
from decimal import Decimal
from uuid import UUID
import asyncio
import aiohttp
import logging
from datetime import datetime

from ..schemas import PaynowPaymentRequest, PaynowPaymentResponse, PaynowStatusResponse, PaymentStatus

logger = logging.getLogger(__name__)

class PaynowIntegration:
    """Paynow payment gateway integration for Zimbabwe"""
    
    def __init__(self, integration_id: str, integration_key: str, return_url: str, result_url: str):
        self.integration_id = integration_id
        self.integration_key = integration_key
        self.return_url = return_url
        self.result_url = result_url
        self.api_url = "https://www.paynow.co.zw/interface/initiatetransaction"
        self.ssl_verify = True
        
    def _generate_hash(self, values: Dict[str, Any]) -> str:
        """Generate hash for Paynow API"""
        # Sort values by key
        sorted_values = sorted(values.items())
        
        # Create concatenated string
        concat_string = ""
        for key, value in sorted_values:
            concat_string += f"{key}={value}&"
        
        # Remove trailing &
        concat_string = concat_string.rstrip('&')
        
        # Add integration key
        concat_string += self.integration_key
        
        # Generate SHA512 hash
        hash_value = hashlib.sha512(concat_string.encode()).hexdigest().upper()
        
        return hash_value
    
    def _verify_hash(self, values: Dict[str, Any], received_hash: str) -> bool:
        """Verify hash from Paynow response"""
        # Remove hash from values before verification
        values_copy = values.copy()
        values_copy.pop('hash', None)
        
        calculated_hash = self._generate_hash(values_copy)
        return calculated_hash == received_hash.upper()
    
    async def initiate_payment(self, payment_request: PaynowPaymentRequest, payment_id: UUID) -> PaynowPaymentResponse:
        """Initiate payment with Paynow"""
        try:
            # Generate unique reference
            reference = f"1CLASS-{payment_id}"
            
            # Build payment data
            payment_data = {
                'id': self.integration_id,
                'reference': reference,
                'amount': str(payment_request.amount),
                'additionalinfo': f"Payment for invoice(s) - Student ID: {payment_request.student_id}",
                'returnurl': self.return_url,
                'resulturl': self.result_url,
                'authemail': payment_request.payer_email,
                'status': 'Message'
            }
            
            # Add phone number if provided
            if payment_request.payer_phone:
                # Clean phone number format
                phone = payment_request.payer_phone.replace('+263', '0').replace(' ', '').replace('-', '')
                if phone.startswith('0'):
                    phone = phone[1:]  # Remove leading 0
                payment_data['phone'] = phone
            
            # Generate hash
            payment_data['hash'] = self._generate_hash(payment_data)
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data=payment_data,
                    ssl=self.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        logger.error(f"Paynow API error: {response.status} - {response_text}")
                        raise Exception(f"Paynow API error: {response.status}")
                    
                    # Parse response
                    response_data = self._parse_response(response_text)
                    
                    # Verify hash
                    if not self._verify_hash(response_data, response_data.get('hash', '')):
                        logger.error("Invalid hash in Paynow response")
                        raise Exception("Invalid response hash from Paynow")
                    
                    # Check if payment initiation was successful
                    status = response_data.get('status', '').lower()
                    if status == 'ok':
                        return PaynowPaymentResponse(
                            payment_id=payment_id,
                            paynow_reference=response_data.get('browserurl', ''),
                            poll_url=response_data.get('pollurl', ''),
                            redirect_url=response_data.get('browserurl', ''),
                            status=status,
                            success=True,
                            hash_valid=True
                        )
                    else:
                        logger.error(f"Paynow payment initiation failed: {response_data}")
                        return PaynowPaymentResponse(
                            payment_id=payment_id,
                            paynow_reference='',
                            poll_url='',
                            redirect_url='',
                            status=status,
                            success=False,
                            hash_valid=True
                        )
        
        except Exception as e:
            logger.error(f"Error initiating Paynow payment: {e}")
            return PaynowPaymentResponse(
                payment_id=payment_id,
                paynow_reference='',
                poll_url='',
                redirect_url='',
                status='error',
                success=False,
                hash_valid=False
            )
    
    async def check_payment_status(self, poll_url: str, payment_id: UUID) -> PaynowStatusResponse:
        """Check payment status using poll URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    poll_url,
                    ssl=self.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        logger.error(f"Paynow status check error: {response.status} - {response_text}")
                        raise Exception(f"Paynow status check error: {response.status}")
                    
                    # Parse response
                    response_data = self._parse_response(response_text)
                    
                    # Verify hash
                    hash_valid = self._verify_hash(response_data, response_data.get('hash', ''))
                    
                    # Map Paynow status to our internal status
                    paynow_status = response_data.get('status', '').lower()
                    internal_status = self._map_paynow_status(paynow_status)
                    
                    return PaynowStatusResponse(
                        payment_id=payment_id,
                        status=internal_status,
                        paynow_reference=response_data.get('reference', ''),
                        amount=Decimal(response_data.get('amount', '0')),
                        success=paynow_status == 'paid',
                        hash_valid=hash_valid,
                        message=response_data.get('statusmessage', '')
                    )
        
        except Exception as e:
            logger.error(f"Error checking Paynow payment status: {e}")
            return PaynowStatusResponse(
                payment_id=payment_id,
                status=PaymentStatus.FAILED,
                paynow_reference='',
                amount=Decimal('0'),
                success=False,
                hash_valid=False,
                message=str(e)
            )
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook from Paynow"""
        try:
            # Verify hash
            hash_valid = self._verify_hash(webhook_data, webhook_data.get('hash', ''))
            
            if not hash_valid:
                logger.error("Invalid hash in Paynow webhook")
                return {
                    'success': False,
                    'error': 'Invalid hash',
                    'hash_valid': False
                }
            
            # Extract payment information
            reference = webhook_data.get('reference', '')
            paynow_status = webhook_data.get('status', '').lower()
            amount = Decimal(webhook_data.get('amount', '0'))
            
            # Map status
            internal_status = self._map_paynow_status(paynow_status)
            
            return {
                'success': True,
                'reference': reference,
                'status': internal_status,
                'amount': amount,
                'paynow_status': paynow_status,
                'hash_valid': hash_valid,
                'raw_data': webhook_data
            }
        
        except Exception as e:
            logger.error(f"Error processing Paynow webhook: {e}")
            return {
                'success': False,
                'error': str(e),
                'hash_valid': False
            }
    
    def _parse_response(self, response_text: str) -> Dict[str, str]:
        """Parse Paynow response text into dictionary"""
        result = {}
        
        for line in response_text.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                result[key.strip()] = urllib.parse.unquote(value.strip())
        
        return result
    
    def _map_paynow_status(self, paynow_status: str) -> PaymentStatus:
        """Map Paynow status to internal PaymentStatus enum"""
        status_mapping = {
            'paid': PaymentStatus.COMPLETED,
            'awaiting delivery': PaymentStatus.COMPLETED,
            'delivered': PaymentStatus.COMPLETED,
            'created': PaymentStatus.PENDING,
            'sent': PaymentStatus.PROCESSING,
            'cancelled': PaymentStatus.CANCELLED,
            'disputed': PaymentStatus.FAILED,
            'refunded': PaymentStatus.REFUNDED,
            'failed': PaymentStatus.FAILED,
            'expired': PaymentStatus.FAILED
        }
        
        return status_mapping.get(paynow_status.lower(), PaymentStatus.FAILED)
    
    async def handle_payment_result(self, payment_id: UUID, status: PaymentStatus, 
                                   paynow_reference: str, amount: Decimal) -> Dict[str, Any]:
        """Handle payment result and update database"""
        try:
            from shared.database import get_database_connection
            
            async with get_database_connection() as conn:
                # Update payment status
                await conn.execute(
                    """
                    UPDATE finance.payments 
                    SET status = $1, gateway_reference = $2, updated_at = NOW()
                    WHERE id = $3
                    """,
                    status.value, paynow_reference, payment_id
                )
                
                # If payment successful, auto-allocate to invoices
                if status == PaymentStatus.COMPLETED:
                    await self._auto_allocate_payment(payment_id, conn)
                
                logger.info(f"Updated payment {payment_id} status to {status.value}")
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status': status.value,
                    'auto_allocated': status == PaymentStatus.COMPLETED
                }
        
        except Exception as e:
            logger.error(f"Error handling payment result: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _auto_allocate_payment(self, payment_id: UUID, conn):
        """Automatically allocate completed payment to outstanding invoices"""
        try:
            # Get payment details
            payment = await conn.fetchrow(
                "SELECT * FROM finance.payments WHERE id = $1",
                payment_id
            )
            
            if not payment:
                return
            
            # Get outstanding invoices for the student
            invoices = await conn.fetch(
                """
                SELECT * FROM finance.invoices 
                WHERE student_id = $1 AND outstanding_amount > 0
                ORDER BY due_date ASC
                """,
                payment['student_id']
            )
            
            if not invoices:
                return
            
            # Allocate payment to invoices
            remaining_amount = payment['amount']
            
            for invoice in invoices:
                if remaining_amount <= 0:
                    break
                
                allocation_amount = min(remaining_amount, invoice['outstanding_amount'])
                
                # Create allocation
                await conn.execute(
                    """
                    INSERT INTO finance.payment_allocations (payment_id, invoice_id, allocated_amount)
                    VALUES ($1, $2, $3)
                    """,
                    payment_id, invoice['id'], allocation_amount
                )
                
                remaining_amount -= allocation_amount
            
            logger.info(f"Auto-allocated payment {payment_id} to {len(invoices)} invoices")
        
        except Exception as e:
            logger.error(f"Error auto-allocating payment: {e}")

# =====================================================
# MOBILE MONEY INTEGRATION
# =====================================================

class MobileMoneyIntegration:
    """Mobile money integration for EcoCash and OneMoney"""
    
    def __init__(self, paynow_integration: PaynowIntegration):
        self.paynow = paynow_integration
    
    async def initiate_ecocash_payment(self, payment_request: PaynowPaymentRequest, 
                                     payment_id: UUID) -> PaynowPaymentResponse:
        """Initiate EcoCash payment"""
        # EcoCash payments use the same Paynow integration
        return await self.paynow.initiate_payment(payment_request, payment_id)
    
    async def initiate_onemoney_payment(self, payment_request: PaynowPaymentRequest, 
                                      payment_id: UUID) -> PaynowPaymentResponse:
        """Initiate OneMoney payment"""
        # OneMoney payments use the same Paynow integration
        return await self.paynow.initiate_payment(payment_request, payment_id)
    
    def generate_ussd_instructions(self, phone_number: str, amount: Decimal) -> Dict[str, str]:
        """Generate USSD instructions for manual payments"""
        instructions = {
            'ecocash': {
                'title': 'EcoCash Payment Instructions',
                'steps': [
                    'Dial *151#',
                    'Select "Send Money"',
                    'Select "To Business"',
                    'Enter business number: 1234567',  # Replace with actual business number
                    f'Enter amount: ${amount}',
                    'Enter PIN to confirm'
                ],
                'note': 'Please send payment confirmation to school after completing payment'
            },
            'onemoney': {
                'title': 'OneMoney Payment Instructions',
                'steps': [
                    'Dial *111#',
                    'Select "Send Money"',
                    'Select "To Business"',
                    'Enter business number: 7654321',  # Replace with actual business number
                    f'Enter amount: ${amount}',
                    'Enter PIN to confirm'
                ],
                'note': 'Please send payment confirmation to school after completing payment'
            }
        }
        
        return instructions

# =====================================================
# PAYMENT FACTORY
# =====================================================

class PaymentGatewayFactory:
    """Factory for creating payment gateway instances"""
    
    @staticmethod
    def create_paynow_integration(config: Dict[str, Any]) -> PaynowIntegration:
        """Create Paynow integration instance"""
        return PaynowIntegration(
            integration_id=config['integration_id'],
            integration_key=config['integration_key'],
            return_url=config['return_url'],
            result_url=config['result_url']
        )
    
    @staticmethod
    def create_mobile_money_integration(paynow_config: Dict[str, Any]) -> MobileMoneyIntegration:
        """Create mobile money integration instance"""
        paynow = PaymentGatewayFactory.create_paynow_integration(paynow_config)
        return MobileMoneyIntegration(paynow)

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def validate_zimbabwe_phone(phone: str) -> bool:
    """Validate Zimbabwe phone number format"""
    import re
    
    # Clean the phone number
    cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    # Check formats: 263771234567, 0771234567
    patterns = [
        r'^263[0-9]{9}$',  # +263 format
        r'^0[0-9]{9}$'     # 0 format
    ]
    
    return any(re.match(pattern, cleaned) for pattern in patterns)

def format_zimbabwe_phone(phone: str) -> str:
    """Format Zimbabwe phone number for API"""
    cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    if cleaned.startswith('263'):
        return f"+{cleaned}"
    elif cleaned.startswith('0'):
        return f"+263{cleaned[1:]}"
    else:
        return f"+263{cleaned}"

def generate_payment_reference(prefix: str = "1CLASS") -> str:
    """Generate unique payment reference"""
    import uuid
    import time
    
    timestamp = str(int(time.time()))
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{prefix}-{timestamp}-{unique_id}".upper()