"""
Minimal encryption utilities for tenant enforcement system
"""

class SchoolEncryption:
    """Minimal encryption class for compatibility"""
    
    def generate_school_key(self, school_id):
        """Generate a simple key for school"""
        return f"key_{school_id}"

# Create instance
school_encryption = SchoolEncryption()

def encrypt_sensitive_field(data, school_id, key):
    """Minimal encryption - just return data as-is for now"""
    return data

def decrypt_sensitive_field(data, school_id, key):
    """Minimal decryption - just return data as-is for now"""
    return data

def encrypt_phone_field(data, school_id, key):
    """Minimal phone encryption - just return data as-is for now"""
    return data

def decrypt_phone_field(data, school_id, key):
    """Minimal phone decryption - just return data as-is for now"""
    return data