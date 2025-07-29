#!/usr/bin/env python3
"""
Test subdomain extraction and tenant context
"""

def test_subdomain_extraction():
    """Test the subdomain extraction logic"""
    
    def extract_subdomain_from_host(host: str):
        """Extract subdomain from host header"""
        if not host:
            return None
        
        # Remove port if present
        clean_host = host.split(':')[0]
        
        # Skip localhost
        if clean_host in ['localhost', '127.0.0.1']:
            return None
        
        parts = clean_host.split('.')
        if len(parts) >= 3 and parts[0] != 'www':
            return parts[0]
        
        return None
    
    # Test cases
    test_cases = [
        ("localhost:3000", None),
        ("127.0.0.1:3000", None),
        ("palm-springs-jnr.oneclass.local:3000", "palm-springs-jnr"),
        ("palm-springs-jnr.oneclass.local", "palm-springs-jnr"),
        ("admin.oneclass.local:3000", "admin"),
        ("oneclass.local:3000", None),
        ("www.oneclass.local:3000", None),
        ("palm-springs-jnr.oneclass.ac.zw", "palm-springs-jnr"),
        ("admin.oneclass.ac.zw", "admin"),
    ]
    
    print("🧪 Testing Subdomain Extraction")
    print("=" * 50)
    
    for host, expected in test_cases:
        result = extract_subdomain_from_host(host)
        status = "✅" if result == expected else "❌"
        print(f"{status} {host:<35} -> {result} (expected: {expected})")
    
    print("\n🎯 Expected Results:")
    print("- palm-springs-jnr.oneclass.local:3000 should extract 'palm-springs-jnr'")
    print("- This should match the school subdomain in the database")
    print("- The tenant middleware should find the school and set context")

if __name__ == "__main__":
    test_subdomain_extraction()
