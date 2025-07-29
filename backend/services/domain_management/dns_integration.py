"""
DNS Integration Service
Handles DNS record management for custom domains
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
import httpx
from pydantic import BaseModel

from shared.config import settings
from shared.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class DNSRecord:
    """DNS record data structure"""
    type: str
    name: str
    content: str
    ttl: int = 300
    priority: Optional[int] = None
    proxied: bool = False


class DNSProviderBase(ABC):
    """Base class for DNS providers"""
    
    @abstractmethod
    async def create_record(self, zone_id: str, record: DNSRecord) -> Dict[str, Any]:
        """Create DNS record"""
        pass
    
    @abstractmethod
    async def update_record(self, zone_id: str, record_id: str, record: DNSRecord) -> Dict[str, Any]:
        """Update DNS record"""
        pass
    
    @abstractmethod
    async def delete_record(self, zone_id: str, record_id: str) -> bool:
        """Delete DNS record"""
        pass
    
    @abstractmethod
    async def list_records(self, zone_id: str, record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List DNS records"""
        pass
    
    @abstractmethod
    async def get_zone_id(self, domain: str) -> Optional[str]:
        """Get zone ID for domain"""
        pass


class CloudflareProvider(DNSProviderBase):
    """Cloudflare DNS provider"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def create_record(self, zone_id: str, record: DNSRecord) -> Dict[str, Any]:
        """Create DNS record in Cloudflare"""
        data = {
            "type": record.type,
            "name": record.name,
            "content": record.content,
            "ttl": record.ttl,
            "proxied": record.proxied
        }
        
        if record.priority is not None:
            data["priority"] = record.priority
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/zones/{zone_id}/dns_records",
                json=data,
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to create DNS record: {response.text}")
                raise ExternalServiceError(f"Failed to create DNS record: {response.text}")
            
            result = response.json()
            if not result.get("success"):
                logger.error(f"Cloudflare API error: {result.get('errors')}")
                raise ExternalServiceError(f"Cloudflare API error: {result.get('errors')}")
            
            return result["result"]
    
    async def update_record(self, zone_id: str, record_id: str, record: DNSRecord) -> Dict[str, Any]:
        """Update DNS record in Cloudflare"""
        data = {
            "type": record.type,
            "name": record.name,
            "content": record.content,
            "ttl": record.ttl,
            "proxied": record.proxied
        }
        
        if record.priority is not None:
            data["priority"] = record.priority
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}",
                json=data,
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update DNS record: {response.text}")
                raise ExternalServiceError(f"Failed to update DNS record: {response.text}")
            
            result = response.json()
            if not result.get("success"):
                logger.error(f"Cloudflare API error: {result.get('errors')}")
                raise ExternalServiceError(f"Cloudflare API error: {result.get('errors')}")
            
            return result["result"]
    
    async def delete_record(self, zone_id: str, record_id: str) -> bool:
        """Delete DNS record from Cloudflare"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to delete DNS record: {response.text}")
                raise ExternalServiceError(f"Failed to delete DNS record: {response.text}")
            
            result = response.json()
            return result.get("success", False)
    
    async def list_records(self, zone_id: str, record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List DNS records from Cloudflare"""
        params = {}
        if record_type:
            params["type"] = record_type
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/zones/{zone_id}/dns_records",
                params=params,
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to list DNS records: {response.text}")
                raise ExternalServiceError(f"Failed to list DNS records: {response.text}")
            
            result = response.json()
            if not result.get("success"):
                logger.error(f"Cloudflare API error: {result.get('errors')}")
                raise ExternalServiceError(f"Cloudflare API error: {result.get('errors')}")
            
            return result["result"]
    
    async def get_zone_id(self, domain: str) -> Optional[str]:
        """Get zone ID for domain from Cloudflare"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/zones",
                params={"name": domain},
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get zone ID: {response.text}")
                return None
            
            result = response.json()
            if not result.get("success") or not result.get("result"):
                return None
            
            return result["result"][0]["id"]


class Route53Provider(DNSProviderBase):
    """AWS Route53 DNS provider"""
    
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region: str = "us-east-1"):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region = region
        # This would use boto3 for AWS API calls
        logger.info("Route53 provider initialized")
    
    async def create_record(self, zone_id: str, record: DNSRecord) -> Dict[str, Any]:
        """Create DNS record in Route53"""
        # Implementation would use boto3 Route53 client
        raise NotImplementedError("Route53 provider not implemented yet")
    
    async def update_record(self, zone_id: str, record_id: str, record: DNSRecord) -> Dict[str, Any]:
        """Update DNS record in Route53"""
        raise NotImplementedError("Route53 provider not implemented yet")
    
    async def delete_record(self, zone_id: str, record_id: str) -> bool:
        """Delete DNS record from Route53"""
        raise NotImplementedError("Route53 provider not implemented yet")
    
    async def list_records(self, zone_id: str, record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List DNS records from Route53"""
        raise NotImplementedError("Route53 provider not implemented yet")
    
    async def get_zone_id(self, domain: str) -> Optional[str]:
        """Get zone ID for domain from Route53"""
        raise NotImplementedError("Route53 provider not implemented yet")


class DNSIntegrationService:
    """DNS integration service"""
    
    def __init__(self):
        self.providers: Dict[str, DNSProviderBase] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize DNS providers"""
        # Initialize Cloudflare provider
        if hasattr(settings, 'CLOUDFLARE_API_TOKEN') and settings.CLOUDFLARE_API_TOKEN:
            self.providers["cloudflare"] = CloudflareProvider(settings.CLOUDFLARE_API_TOKEN)
        
        # Initialize Route53 provider
        if (hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID and
            hasattr(settings, 'AWS_SECRET_ACCESS_KEY') and settings.AWS_SECRET_ACCESS_KEY):
            self.providers["route53"] = Route53Provider(
                settings.AWS_ACCESS_KEY_ID,
                settings.AWS_SECRET_ACCESS_KEY
            )
    
    def get_provider(self, provider_name: str) -> DNSProviderBase:
        """Get DNS provider by name"""
        if provider_name not in self.providers:
            raise ValueError(f"DNS provider '{provider_name}' not configured")
        return self.providers[provider_name]
    
    async def setup_domain_dns(self, domain: str, subdomain: str, server_ip: str, provider_name: str = "cloudflare") -> List[Dict[str, Any]]:
        """Set up DNS records for a domain"""
        provider = self.get_provider(provider_name)
        
        # Get zone ID for base domain
        zone_id = await provider.get_zone_id("oneclass.ac.zw")
        if not zone_id:
            raise ExternalServiceError("Cannot find zone for oneclass.ac.zw")
        
        # Define DNS records for the subdomain
        records = [
            DNSRecord(
                type="A",
                name=f"{subdomain}.oneclass.ac.zw",
                content=server_ip,
                ttl=300,
                proxied=True  # Enable Cloudflare proxy
            ),
            DNSRecord(
                type="CNAME",
                name=f"www.{subdomain}.oneclass.ac.zw",
                content=f"{subdomain}.oneclass.ac.zw",
                ttl=300,
                proxied=True
            ),
            DNSRecord(
                type="MX",
                name=f"{subdomain}.oneclass.ac.zw",
                content=f"mail.oneclass.ac.zw",
                ttl=300,
                priority=10
            ),
            DNSRecord(
                type="TXT",
                name=f"_dmarc.{subdomain}.oneclass.ac.zw",
                content="v=DMARC1; p=quarantine; rua=mailto:dmarc@oneclass.ac.zw",
                ttl=300
            ),
            DNSRecord(
                type="TXT",
                name=f"{subdomain}.oneclass.ac.zw",
                content="v=spf1 include:_spf.oneclass.ac.zw ~all",
                ttl=300
            )
        ]
        
        # Create DNS records
        created_records = []
        for record in records:
            try:
                result = await provider.create_record(zone_id, record)
                created_records.append(result)
                logger.info(f"Created DNS record: {record.type} {record.name} -> {record.content}")
            except Exception as e:
                logger.error(f"Failed to create DNS record {record.type} {record.name}: {str(e)}")
                # Continue with other records
        
        return created_records
    
    async def create_verification_record(self, domain: str, subdomain: str, verification_token: str, provider_name: str = "cloudflare") -> Dict[str, Any]:
        """Create DNS verification record"""
        provider = self.get_provider(provider_name)
        
        # Get zone ID for base domain
        zone_id = await provider.get_zone_id("oneclass.ac.zw")
        if not zone_id:
            raise ExternalServiceError("Cannot find zone for oneclass.ac.zw")
        
        # Create verification TXT record
        record = DNSRecord(
            type="TXT",
            name=f"_oneclass-verification.{subdomain}.oneclass.ac.zw",
            content=f"oneclass-verification={verification_token}",
            ttl=300
        )
        
        result = await provider.create_record(zone_id, record)
        logger.info(f"Created verification record for {subdomain}.oneclass.ac.zw")
        
        return result
    
    async def verify_domain_ownership(self, domain: str, subdomain: str, verification_token: str, provider_name: str = "cloudflare") -> bool:
        """Verify domain ownership via DNS record"""
        provider = self.get_provider(provider_name)
        
        # Get zone ID for base domain
        zone_id = await provider.get_zone_id("oneclass.ac.zw")
        if not zone_id:
            return False
        
        # List TXT records for verification
        try:
            records = await provider.list_records(zone_id, "TXT")
            
            # Check for verification record
            verification_name = f"_oneclass-verification.{subdomain}.oneclass.ac.zw"
            verification_content = f"oneclass-verification={verification_token}"
            
            for record in records:
                if (record.get("name") == verification_name and 
                    record.get("content") == verification_content):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify domain ownership: {str(e)}")
            return False
    
    async def cleanup_domain_dns(self, domain: str, subdomain: str, provider_name: str = "cloudflare") -> bool:
        """Clean up DNS records for a domain"""
        provider = self.get_provider(provider_name)
        
        # Get zone ID for base domain
        zone_id = await provider.get_zone_id("oneclass.ac.zw")
        if not zone_id:
            return False
        
        # List all records for the subdomain
        try:
            records = await provider.list_records(zone_id)
            
            # Find records that match the subdomain
            subdomain_records = [
                record for record in records
                if f"{subdomain}.oneclass.ac.zw" in record.get("name", "")
            ]
            
            # Delete matching records
            deleted_count = 0
            for record in subdomain_records:
                try:
                    await provider.delete_record(zone_id, record["id"])
                    deleted_count += 1
                    logger.info(f"Deleted DNS record: {record['type']} {record['name']}")
                except Exception as e:
                    logger.error(f"Failed to delete DNS record {record['id']}: {str(e)}")
            
            logger.info(f"Cleaned up {deleted_count} DNS records for {subdomain}.oneclass.ac.zw")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup DNS records: {str(e)}")
            return False
    
    async def get_domain_records(self, domain: str, subdomain: str, provider_name: str = "cloudflare") -> List[Dict[str, Any]]:
        """Get DNS records for a domain"""
        provider = self.get_provider(provider_name)
        
        # Get zone ID for base domain
        zone_id = await provider.get_zone_id("oneclass.ac.zw")
        if not zone_id:
            return []
        
        # List all records for the subdomain
        try:
            records = await provider.list_records(zone_id)
            
            # Filter records that match the subdomain
            subdomain_records = [
                record for record in records
                if f"{subdomain}.oneclass.ac.zw" in record.get("name", "")
            ]
            
            return subdomain_records
            
        except Exception as e:
            logger.error(f"Failed to get DNS records: {str(e)}")
            return []