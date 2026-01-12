"""
Unit tests for authentication system.

Tests JWT token creation, password hashing, user registration,
login, logout, and role-based access control.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole, TokenBlacklist
from app.auth.security import get_password_hash, verify_password, validate_password
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    """Create test database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Create an admin access token."""
    token_data = {
        "sub": admin_user.id,
        "email": admin_user.email,
        "role": admin_user.role.value
    }
    return create_access_token(token_data)


@pytest.fixture
def user_token(test_user):
    """Create a user access token."""
    token_data = {
        "sub": test_user.id,
        "email": test_user.email,
        "role": test_user.role.value
    }
    return create_access_token(token_data)


# Password Security Tests

def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123!"
    hashed = get_password_hash(password)

    # Password should be hashed (not plain text)
    assert password != hashed
    assert hashed.startswith("$2b$")

    # Verification should work
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_password_validation():
    """Test password validation rules."""
    # Valid password
    is_valid, msg = validate_password("ValidPass123!")
    assert is_valid is True
    assert msg == ""

    # Too short
    is_valid, msg = validate_password("Short1!")
    assert is_valid is False
    assert "at least" in msg

    # No uppercase
    is_valid, msg = validate_password("noupppercase123!")
    assert is_valid is False
    assert "uppercase" in msg

    # No lowercase
    is_valid, msg = validate_password("NOLOWERCASE123!")
    assert is_valid is False
    assert "lowercase" in msg

    # No digit
    is_valid, msg = validate_password("NoDigits!")
    assert is_valid is False
    assert "digit" in msg

    # No special character
    is_valid, msg = validate_password("NoSpecial123")
    assert is_valid is False
    assert "special" in msg


# JWT Token Tests

def test_create_access_token():
    """Test JWT access token creation."""
    data = {"sub": 1, "email": "test@example.com", "role": "user"}
    token = create_access_token(data)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == 1
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test JWT refresh token creation."""
    data = {"sub": 1}
    token = create_refresh_token(data)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == 1
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    """Test decoding invalid token."""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)
    assert payload is None


# Authentication Endpoint Tests

def test_login_success(db, test_user):
    """Test successful login."""
    # Temporarily disable auth requirement for this test
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123!"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password(db, test_user):
    """Test login with wrong password."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(db):
    """Test login with non-existent user."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 401


def test_get_current_user(db, test_user, user_token):
    """Test getting current user information."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "USER"
    assert data["is_active"] is True


def test_get_current_user_no_token(db):
    """Test getting current user without token."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = True

    response = client.get("/api/auth/me")

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 401


# User Registration Tests

def test_register_user_admin_only(db, admin_user, admin_token):
    """Test user registration (admin only)."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "newuser@example.com",
            "password": "NewUserPass123!",
            "full_name": "New User",
            "role": "user"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "USER"


def test_register_duplicate_email(db, admin_user, admin_token, test_user):
    """Test registering user with duplicate email."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "test@example.com",  # Already exists
            "password": "NewUserPass123!",
            "full_name": "Duplicate User",
            "role": "user"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_weak_password(db, admin_user, admin_token):
    """Test registering user with weak password."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "newuser@example.com",
            "password": "weak",  # Too weak
            "full_name": "New User",
            "role": "user"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 400


# Token Refresh Tests

def test_refresh_token(db, test_user):
    """Test refreshing access token."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    # Create refresh token
    refresh_token = create_refresh_token({"sub": test_user.id})

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_invalid(db):
    """Test refreshing with invalid token."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid.token.here"}
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 401


# Role-Based Access Control Tests

def test_admin_access_user_list(db, admin_user, admin_token):
    """Test admin can access user list."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)


def test_user_cannot_access_admin_endpoint(db, test_user, user_token):
    """Test regular user cannot access admin endpoints."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 403


# Logout Tests

def test_logout(db, test_user, user_token):
    """Test user logout."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 204


# Password Change Tests

def test_change_password(db, test_user, user_token):
    """Test changing password."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "current_password": "TestPass123!",
            "new_password": "NewTestPass123!"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 204


def test_change_password_wrong_current(db, test_user, user_token):
    """Test changing password with wrong current password."""
    original_require_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = False

    response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "current_password": "WrongPassword",
            "new_password": "NewTestPass123!"
        }
    )

    settings.REQUIRE_AUTH = original_require_auth

    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()
