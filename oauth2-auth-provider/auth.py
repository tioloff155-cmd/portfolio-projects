"""
OAuth2 Auth Provider
A stateless JWT-based identity provider for multi-tenant
backend security. Supports user registration, login,
token refresh, and role-based access control.
"""

import hashlib
import hmac
import json
import time
import base64
import uuid
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Role(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SERVICE = "SERVICE"


@dataclass
class User:
    user_id: str
    email: str
    password_hash: str
    salt: str
    role: Role = Role.USER
    tenant_id: str = "default"
    created_at: float = field(default_factory=time.time)
    active: bool = True


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class AuthProvider:
    """
    Core identity provider. Handles credential storage, JWT issuance,
    and token verification without any external library dependency.
    """

    ACCESS_TTL = 3600       # 1 hour
    REFRESH_TTL = 86400 * 7  # 7 days

    def __init__(self, secret_key: str = "change-me-in-production"):
        self._secret = secret_key.encode()
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}
        self._refresh_store: dict[str, dict] = {}

    # --- User management ---

    def register(self, email: str, password: str, role: Role = Role.USER, tenant_id: str = "default") -> User:
        if email in self._email_index:
            raise ValueError(f"Email already registered: {email}")

        salt = os.urandom(16).hex()
        pw_hash = self._hash_password(password, salt)
        user = User(
            user_id=uuid.uuid4().hex[:12],
            email=email,
            password_hash=pw_hash,
            salt=salt,
            role=role,
            tenant_id=tenant_id,
        )
        self._users[user.user_id] = user
        self._email_index[email] = user.user_id
        return user

    def authenticate(self, email: str, password: str) -> Optional[TokenPair]:
        uid = self._email_index.get(email)
        if not uid:
            return None
        user = self._users[uid]
        if not user.active:
            return None
        if self._hash_password(password, user.salt) != user.password_hash:
            return None
        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> Optional[TokenPair]:
        payload = self._decode_jwt(refresh_token)
        if not payload:
            return None
        if payload.get("type") != "refresh":
            return None
        uid = payload.get("sub")
        if uid not in self._users:
            return None
        return self._issue_tokens(self._users[uid])

    def verify(self, access_token: str) -> Optional[dict]:
        payload = self._decode_jwt(access_token)
        if not payload:
            return None
        if payload.get("type") != "access":
            return None
        return payload

    def require_role(self, token: str, required: Role) -> bool:
        payload = self.verify(token)
        if not payload:
            return False
        role_hierarchy = {Role.USER.value: 0, Role.ADMIN.value: 1, Role.SERVICE.value: 2}
        user_level = role_hierarchy.get(payload.get("role", ""), -1)
        required_level = role_hierarchy.get(required.value, 99)
        return user_level >= required_level

    # --- JWT implementation (no external deps) ---

    def _issue_tokens(self, user: User) -> TokenPair:
        now = int(time.time())
        access_payload = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "tenant": user.tenant_id,
            "type": "access",
            "iat": now,
            "exp": now + self.ACCESS_TTL,
        }
        refresh_payload = {
            "sub": user.user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + self.REFRESH_TTL,
        }
        return TokenPair(
            access_token=self._encode_jwt(access_payload),
            refresh_token=self._encode_jwt(refresh_payload),
            expires_in=self.ACCESS_TTL,
        )

    def _encode_jwt(self, payload: dict) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        h = self._b64url(json.dumps(header).encode())
        p = self._b64url(json.dumps(payload).encode())
        signature = hmac.new(self._secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
        s = self._b64url(signature)
        return f"{h}.{p}.{s}"

    def _decode_jwt(self, token: str) -> Optional[dict]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            h, p, s = parts
            expected_sig = hmac.new(self._secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
            actual_sig = self._b64url_decode(s)
            if not hmac.compare_digest(expected_sig, actual_sig):
                return None
            payload = json.loads(self._b64url_decode(p))
            if payload.get("exp", 0) < time.time():
                return None
            return payload
        except Exception:
            return None

    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _b64url_decode(self, s: str) -> bytes:
        padding = 4 - len(s) % 4
        return base64.urlsafe_b64decode(s + "=" * padding)

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


if __name__ == "__main__":
    auth = AuthProvider(secret_key="my-super-secret-key")

    # Register users
    admin = auth.register("admin@company.com", "S3cur3P@ss!", role=Role.ADMIN)
    user = auth.register("dev@company.com", "devpass123", role=Role.USER)
    print(f"Registered: {admin.email} ({admin.role.value})")
    print(f"Registered: {user.email} ({user.role.value})")

    # Authenticate
    tokens = auth.authenticate("admin@company.com", "S3cur3P@ss!")
    if tokens:
        print(f"\nAdmin access_token: {tokens.access_token[:50]}...")
        print(f"Expires in: {tokens.expires_in}s")

        # Verify
        payload = auth.verify(tokens.access_token)
        print(f"Verified payload: sub={payload['sub']}, role={payload['role']}, tenant={payload['tenant']}")

        # Role check
        print(f"Has ADMIN role: {auth.require_role(tokens.access_token, Role.ADMIN)}")
        print(f"Has SERVICE role: {auth.require_role(tokens.access_token, Role.SERVICE)}")

        # Refresh
        new_tokens = auth.refresh(tokens.refresh_token)
        print(f"\nRefreshed token: {new_tokens.access_token[:50]}...")

    # Failed auth
    bad = auth.authenticate("admin@company.com", "wrongpassword")
    print(f"\nBad login result: {bad}")
