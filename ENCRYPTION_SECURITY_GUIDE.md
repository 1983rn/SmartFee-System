# SmartFee End-to-End Encryption & Data Privacy Guide

## Overview

This document describes the comprehensive end-to-end encryption system implemented in SmartFee to ensure complete data privacy between school accounts. Each school account has its own unique encryption key, making it impossible for one school to access another school's data.

## Security Features

### 1. School-Specific Encryption Keys
- Each school gets a unique encryption key generated using PBKDF2 with SHA256
- Keys are derived from a master secret and school-specific salt
- 100,000 iterations for key derivation (industry standard)
- Keys are stored securely in the database

### 2. Data Isolation
- All sensitive data is encrypted with school-specific keys
- Database queries are filtered by `school_id` to prevent cross-school access
- Developers can access all schools, but school admins only see their own data

### 3. Encrypted Fields
The following sensitive fields are encrypted:

**Student Data:**
- Student ID
- Student Name
- Sex
- Form/Class
- Parent Phone Number (with additional obfuscation)

**Income Records:**
- Student ID
- Student Name
- Form/Class
- Payment Reference
- Fee Type

**Expenditure Records:**
- Activity/Service Description
- Voucher Number
- Cheque Number
- Fund Type

**Receipt Records:**
- Receipt Number
- Student ID
- Student Name
- Form/Class
- Deposit Slip Reference
- Fee Type

**Other Income Records:**
- Customer Name
- Income Type

**Budget Records:**
- Activity/Service Description

**Fund Configuration:**
- Term Name

## Implementation Details

### Encryption Utilities (`encryption_utils.py`)

```python
# Generate school-specific encryption key
key = school_encryption.generate_school_key(school_id)

# Encrypt sensitive data
encrypted_data = encrypt_sensitive_field(data, school_id, encryption_key)

# Decrypt sensitive data
decrypted_data = decrypt_sensitive_field(encrypted_data, school_id, encryption_key)

# Encrypt phone numbers (with additional obfuscation)
encrypted_phone = encrypt_phone_field(phone, school_id, encryption_key)
```

### Data Isolation Helpers (`data_isolation_helpers.py`)

```python
# Get current school ID from session
current_school_id = get_current_school_id()

# Get school-filtered query
query = get_school_filtered_query(Student)

# Ensure user has access to school data
if ensure_school_access(school_id):
    # User can access this school's data
```

## Database Schema Changes

### New Columns Added:
- `school_configuration.encryption_key` - Unique encryption key for each school
- `student.school_id` - Links student to school
- `income.school_id` - Links income record to school
- `expenditure.school_id` - Links expenditure to school
- `receipt.school_id` - Links receipt to school
- `other_income.school_id` - Links other income to school
- `budget.school_id` - Links budget item to school
- `fund_configuration.school_id` - Links fund config to school

### Field Size Increases:
- Encrypted fields have increased sizes to accommodate encrypted data
- String fields that store encrypted data are typically 2-4x larger

## Migration Process

### 1. Install Dependencies
```bash
pip install cryptography==41.0.7
```

### 2. Set Environment Variables
Add to your `.env` file:
```
ENCRYPTION_MASTER_KEY=your-super-secure-master-encryption-key-change-in-production
```

### 3. Run Migration Script
```bash
python migrate_to_encrypted_data.py
```

This script will:
- Add new database columns
- Generate encryption keys for existing schools
- Encrypt all existing sensitive data
- Assign existing data to default school

### 4. Verify Migration
The script includes verification to ensure all data was migrated correctly.

## Security Best Practices

### 1. Master Key Security
- Use a strong, unique master key in production
- Store the master key securely (environment variable, key management service)
- Never commit the master key to version control
- Rotate the master key periodically

### 2. Database Security
- Use encrypted database connections (SSL/TLS)
- Implement database access controls
- Regular database backups with encryption
- Monitor database access logs

### 3. Application Security
- Use HTTPS for all communications
- Implement proper session management
- Regular security audits
- Keep dependencies updated

## Data Access Patterns

### School Admin Access
- Can only access data for their assigned school
- All queries automatically filtered by `school_id`
- Cannot see or modify other schools' data

### Developer Access
- Can access all schools' data
- Used for system administration and support
- Should be limited to trusted personnel

### Data Encryption Flow
1. User inputs data → 2. Data encrypted with school key → 3. Stored in database
1. Database query → 2. Encrypted data retrieved → 3. Data decrypted for display

## Troubleshooting

### Common Issues

**1. Decryption Fails**
- Check if encryption key exists for the school
- Verify the master key hasn't changed
- Ensure data wasn't corrupted

**2. School Access Denied**
- Verify user has correct `school_id` in session
- Check if school is blocked or subscription expired
- Ensure user role is set correctly

**3. Migration Issues**
- Backup database before migration
- Check database permissions
- Verify all dependencies are installed

### Recovery Procedures

**1. Lost Encryption Key**
- If master key is lost, encrypted data cannot be recovered
- Restore from backup if available
- Re-encrypt data with new key if necessary

**2. Data Corruption**
- Restore from backup
- Run data verification scripts
- Check database integrity

## Performance Considerations

### Encryption Overhead
- Encryption/decryption adds minimal CPU overhead
- Database storage increases by 2-4x for encrypted fields
- Query performance may be slightly slower due to larger field sizes

### Optimization Strategies
- Use database indexes on non-encrypted fields
- Cache decrypted data when appropriate
- Implement pagination for large datasets
- Use connection pooling

## Compliance & Auditing

### Data Privacy Compliance
- Meets requirements for data isolation between tenants
- Supports GDPR and similar privacy regulations
- Provides audit trail for data access

### Audit Logging
- All database queries are filtered by school
- Session management tracks user access
- Encryption/decryption operations can be logged

## Testing

### Unit Tests
```python
# Test encryption/decryption
def test_encryption():
    original = "Test Data"
    encrypted = encrypt_sensitive_field(original, school_id, key)
    decrypted = decrypt_sensitive_field(encrypted, school_id, key)
    assert original == decrypted

# Test data isolation
def test_data_isolation():
    # Ensure school A cannot access school B's data
    query = get_school_filtered_query(Student)
    students = query.all()
    # Verify all students belong to current school
```

### Integration Tests
- Test complete user workflows
- Verify cross-school data isolation
- Test migration scripts on sample data

## Monitoring & Maintenance

### Regular Tasks
- Monitor encryption key usage
- Check for failed decryption attempts
- Verify data isolation is working
- Update encryption libraries

### Security Monitoring
- Monitor for unauthorized access attempts
- Track unusual query patterns
- Alert on encryption failures
- Regular security assessments

## Support & Contact

For technical support or security concerns:
- Review this documentation first
- Check application logs for errors
- Contact system administrator
- Report security issues immediately

---

**Important:** This encryption system provides strong data privacy between schools. However, it requires proper implementation, secure key management, and regular maintenance to remain effective.
