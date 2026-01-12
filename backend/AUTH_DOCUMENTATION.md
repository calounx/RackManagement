# HomeRack Authentication System Documentation

## Overview

The HomeRack application uses JWT (JSON Web Token) based authentication with role-based access control (RBAC). This document provides comprehensive information about the authentication system implementation.

## Table of Contents

1. [Architecture](#architecture)
2. [Authentication Flow](#authentication-flow)
3. [API Endpoints](#api-endpoints)
4. [Security Features](#security-features)
5. [Configuration](#configuration)
6. [Database Schema](#database-schema)
7. [Testing](#testing)
8. [Deployment](#deployment)

---

## Architecture

### Components

```
backend/app/
├── auth/
│   ├── __init__.py         # Auth module exports
│   ├── jwt.py              # JWT token creation and validation
│   ├── security.py         # Password hashing and validation
│   └── deps.py             # FastAPI dependencies for auth
├── api/
│   └── auth.py             # Authentication endpoints
├── models.py               # User and TokenBlacklist models
└── schemas.py              # Auth-related Pydantic schemas
```

### Key Technologies

- **JWT**: JSON Web Tokens for stateless authentication
- **bcrypt**: Secure password hashing algorithm
- **python-jose**: JWT encoding/decoding
- **passlib**: Password hashing utilities
- **FastAPI Security**: OAuth2 password bearer flow

---

## Authentication Flow

### 1. User Registration (Admin Only)

```
POST /api/auth/register
Authorization: Bearer <admin_token>
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "user"
}
```

### 2. User Login

```
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

Response:
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Using Access Token

```
GET /api/protected-endpoint
Authorization: Bearer <access_token>
```

### 4. Refreshing Token

```
POST /api/auth/refresh
{
  "refresh_token": "eyJhbGci..."
}
```

### 5. Logout

```
POST /api/auth/logout
Authorization: Bearer <access_token>
```

---

## API Endpoints

### Public Endpoints (No Authentication Required)

- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /health` - Health check
- `GET /` - API root

### Authenticated Endpoints

#### User Endpoints

- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/me` - Update current user
- `POST /api/auth/change-password` - Change password
- `POST /api/auth/logout` - Logout

#### Admin-Only Endpoints

- `POST /api/auth/register` - Register new user
- `GET /api/users` - List all users
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user by ID
- `DELETE /api/users/{id}` - Delete user by ID

### Protected Resource Endpoints

All other API endpoints (devices, racks, etc.) are protected when `REQUIRE_AUTH=true`.

---

## Security Features

### 1. Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters (configurable via `PASSWORD_MIN_LENGTH`)
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*(),.?":{}|<>)

### 2. Password Hashing

- **Algorithm**: bcrypt with salt rounds
- **Storage**: Only hashed passwords stored in database
- **Verification**: Constant-time comparison

### 3. JWT Tokens

#### Access Token
- **Lifetime**: 30 minutes (configurable)
- **Use**: API authentication
- **Contains**: user_id, email, role, jti (for blacklisting)

#### Refresh Token
- **Lifetime**: 7 days (configurable)
- **Use**: Obtaining new access tokens
- **Contains**: user_id, jti (for blacklisting)

### 4. Token Blacklisting

Tokens can be blacklisted on logout to prevent reuse. The `token_blacklist` table stores:
- Token JTI (unique identifier)
- User ID
- Expiration time

### 5. Role-Based Access Control (RBAC)

Three roles are supported:

| Role     | Permissions                                      |
|----------|--------------------------------------------------|
| admin    | Full access to all endpoints, user management   |
| user     | Read/write access to devices, racks, etc.       |
| readonly | Read-only access to resources                   |

### 6. Rate Limiting

Authentication endpoints are rate-limited:
- Login: 5 attempts per minute per IP
- Other endpoints: 300 requests per hour

### 7. Optional Authentication

Set `REQUIRE_AUTH=false` for development/testing to make authentication optional.

---

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-use-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Authentication Behavior
REQUIRE_AUTH=true  # Set to false for testing without auth
PASSWORD_MIN_LENGTH=8

# Rate Limiting
RATE_LIMIT_AUTH_ENDPOINTS=5/minute
```

### Generating Secure Secret Key

```bash
# Generate a secure random secret key
openssl rand -hex 32
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role ENUM('ADMIN', 'USER', 'READONLY') NOT NULL DEFAULT 'USER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_login DATETIME,
    INDEX ix_users_email (email),
    INDEX ix_users_role (role),
    INDEX ix_users_email_active (email, is_active)
);
```

### Token Blacklist Table

```sql
CREATE TABLE token_blacklist (
    id INTEGER PRIMARY KEY,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX ix_token_blacklist_jti (token_jti),
    INDEX ix_token_blacklist_expires (expires_at)
);
```

---

## Testing

### Running Tests

```bash
# Run all auth tests
cd backend
pytest tests/unit/test_auth.py -v

# Run specific test
pytest tests/unit/test_auth.py::test_login_success -v

# Run with coverage
pytest tests/unit/test_auth.py --cov=app.auth --cov-report=html
```

### Test Coverage

The test suite covers:
- Password hashing and validation
- JWT token creation and validation
- User registration
- Login/logout
- Token refresh
- Password changes
- Role-based access control
- Error handling

### Manual Testing with cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@homerack.local&password=Admin123!"

# Get current user
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

# Register new user (admin only)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!","role":"user"}'
```

---

## Deployment

### Initial Setup

1. **Set environment variables** in production:
   ```bash
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   REQUIRE_AUTH=true
   ```

2. **Run database migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Create admin user**:
   ```bash
   python scripts/create_admin_user.py \
     --email admin@yourcompany.com \
     --password YourSecurePassword123!
   ```

4. **Change default password** immediately after first login.

### Production Checklist

- [ ] Generate and set strong `JWT_SECRET_KEY`
- [ ] Set `REQUIRE_AUTH=true`
- [ ] Configure HTTPS/TLS for all endpoints
- [ ] Enable rate limiting
- [ ] Set up monitoring for failed login attempts
- [ ] Configure CORS properly
- [ ] Implement token rotation policy
- [ ] Set up automated token cleanup (blacklist)
- [ ] Enable audit logging for auth events
- [ ] Configure secure cookie settings
- [ ] Implement IP whitelisting for admin endpoints (optional)

### Security Best Practices

1. **Token Storage (Frontend)**:
   - Store access tokens in memory (not localStorage)
   - Store refresh tokens in httpOnly cookies or secure storage
   - Clear tokens on logout

2. **Token Rotation**:
   - Implement automatic token refresh before expiration
   - Rotate refresh tokens on each use

3. **Monitoring**:
   - Log all authentication events
   - Monitor for brute force attacks
   - Alert on suspicious activity

4. **Database Security**:
   - Use connection pooling
   - Enable SSL/TLS for database connections
   - Implement backup and recovery procedures

---

## Code Examples

### Protecting Endpoints

```python
from fastapi import Depends, APIRouter
from app.auth.deps import get_current_active_user, require_admin
from app.models import User

router = APIRouter()

# Require any authenticated user
@router.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": f"Hello, {current_user.email}"}

# Require admin role
@router.delete("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(require_admin)
):
    return {"message": "Admin access granted"}

# Custom role check
from app.auth.deps import require_role

@router.post("/manager-only", dependencies=[Depends(require_role("admin", "manager"))])
async def manager_endpoint():
    return {"message": "Manager access granted"}
```

### Creating Tokens

```python
from app.auth.jwt import create_access_token, create_refresh_token

# Create access token
token_data = {
    "sub": user.id,
    "email": user.email,
    "role": user.role.value
}
access_token = create_access_token(token_data)

# Create refresh token
refresh_token = create_refresh_token({"sub": user.id})
```

### Password Operations

```python
from app.auth.security import get_password_hash, verify_password, validate_password

# Hash password
hashed = get_password_hash("MyPassword123!")

# Verify password
is_valid = verify_password("MyPassword123!", hashed)

# Validate password strength
is_valid, error_msg = validate_password("MyPassword123!")
if not is_valid:
    raise ValueError(error_msg)
```

---

## Troubleshooting

### Common Issues

1. **401 Unauthorized**:
   - Check if token is included in Authorization header
   - Verify token hasn't expired
   - Ensure user is active

2. **403 Forbidden**:
   - Check user role permissions
   - Verify endpoint requires correct role

3. **Token Expired**:
   - Use refresh token to get new access token
   - Implement automatic token refresh in frontend

4. **Password Validation Failed**:
   - Ensure password meets all requirements
   - Check PASSWORD_MIN_LENGTH setting

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

---

## Support

For issues or questions:
1. Check this documentation
2. Review test cases in `tests/unit/test_auth.py`
3. Check logs for detailed error messages
4. Consult FastAPI security documentation

---

## License

Copyright (c) 2026 HomeRack Project
