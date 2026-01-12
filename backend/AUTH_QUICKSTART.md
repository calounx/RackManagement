# Authentication Quick Start Guide

## Initial Setup (5 minutes)

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Generate secure JWT secret
openssl rand -hex 32

# Edit .env and set:
JWT_SECRET_KEY=<generated-key-from-above>
REQUIRE_AUTH=true
```

### 3. Run Database Migrations

```bash
# Apply migrations to create auth tables
alembic upgrade head
```

### 4. Create Admin User

```bash
# Create default admin user
python scripts/create_admin_user.py

# Or with custom credentials:
python scripts/create_admin_user.py \
  --email admin@example.com \
  --password YourSecurePass123!
```

**Default Credentials:**
- Email: `admin@homerack.local`
- Password: `Admin123!`

**⚠️ IMPORTANT: Change the default password immediately!**

### 5. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

---

## Testing Authentication

### Login and Get Token

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@homerack.local&password=Admin123!"

# Save the access_token from response
export TOKEN="eyJhbGciOi..."
```

### Test Protected Endpoint

```bash
# Get current user info
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Create New User (Admin Only)

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "UserPass123!",
    "full_name": "John Doe",
    "role": "user"
  }'
```

---

## Common Operations

### Change Password

```bash
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "Admin123!",
    "new_password": "NewSecurePass123!"
  }'
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<your-refresh-token>"
  }'
```

### List Users (Admin)

```bash
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer $TOKEN"
```

---

## Frontend Integration

### Login Flow

```typescript
// Login
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'admin@homerack.local',
    password: 'Admin123!'
  })
});

const { access_token, refresh_token } = await response.json();

// Store tokens (example - use secure storage in production)
sessionStorage.setItem('access_token', access_token);
sessionStorage.setItem('refresh_token', refresh_token);
```

### Making Authenticated Requests

```typescript
const token = sessionStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/racks', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Auto Token Refresh

```typescript
async function refreshToken() {
  const refresh_token = sessionStorage.getItem('refresh_token');

  const response = await fetch('http://localhost:8000/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });

  const { access_token } = await response.json();
  sessionStorage.setItem('access_token', access_token);

  return access_token;
}

// Call before token expires or on 401 response
```

---

## Development Mode (No Auth)

For development/testing without authentication:

```bash
# In .env
REQUIRE_AUTH=false
```

All endpoints will be accessible without tokens. **Never use in production!**

---

## User Roles

| Role     | Permissions                           |
|----------|---------------------------------------|
| admin    | Full access, user management          |
| user     | Create/read/update/delete resources   |
| readonly | Read-only access                      |

---

## Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

---

## Rate Limiting

- **Login**: 5 attempts per minute
- **General API**: 300 requests per hour
- **Thermal Analysis**: 10 per minute

---

## Troubleshooting

### "Not authenticated" error
- Check if token is included in Authorization header
- Format: `Authorization: Bearer <token>`
- Verify token hasn't expired (30 minutes)

### "Insufficient permissions" error
- Check user role matches endpoint requirements
- Admin-only endpoints require admin role

### "Token expired" error
- Use refresh token to get new access token
- Implement automatic token refresh in frontend

### Can't login
- Verify credentials are correct
- Check if user is active
- Review server logs for details

---

## API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Next Steps

1. ✅ Change default admin password
2. ✅ Create additional user accounts
3. ✅ Configure frontend authentication
4. ✅ Test protected endpoints
5. ✅ Review AUTH_DOCUMENTATION.md for details
6. ✅ Run test suite: `pytest tests/unit/test_auth.py`

---

## Production Deployment

Before deploying to production:

1. **Generate secure keys**:
   ```bash
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Enable authentication**:
   ```bash
   REQUIRE_AUTH=true
   ```

3. **Use HTTPS only** - Never send tokens over HTTP

4. **Configure CORS** properly for your domain

5. **Enable rate limiting**

6. **Set up monitoring** and alerts

See AUTH_DOCUMENTATION.md for complete production checklist.

---

## Quick Reference

```bash
# Environment Variables
JWT_SECRET_KEY=<secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REQUIRE_AUTH=true
PASSWORD_MIN_LENGTH=8

# Endpoints
POST   /api/auth/login          - Login
POST   /api/auth/logout         - Logout
POST   /api/auth/register       - Register (admin)
POST   /api/auth/refresh        - Refresh token
GET    /api/auth/me             - Current user
PUT    /api/auth/me             - Update user
POST   /api/auth/change-password - Change password
GET    /api/users               - List users (admin)
GET    /api/users/{id}          - Get user (admin)
PUT    /api/users/{id}          - Update user (admin)
DELETE /api/users/{id}          - Delete user (admin)
```
