"""RS256 key pair management for JWT signing.

In production, keys should be stored in AWS Secrets Manager / HashiCorp Vault.
This module handles PEM loading, generation, and rotation.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_key_pair(key_size: int = 4096) -> tuple[bytes, bytes]:
    """Generate a new RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def load_private_key(key_path: str) -> bytes:
    """Load private key PEM from file."""
    path = Path(key_path)
    if not path.exists():
        priv, pub = generate_key_pair()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(priv)
        pub_path = path.with_suffix(".pub.pem")
        pub_path.write_bytes(pub)
        return priv
    return path.read_bytes()


def get_signing_key() -> tuple[bytes, Optional[bytes]]:
    """Get the signing key pair. Uses env var path or generates on first run."""
    key_path = os.environ.get("JWT_PRIVATE_KEY_PATH", "")
    if key_path:
        private_pem = load_private_key(key_path)
        public_path = Path(key_path).with_suffix(".pub.pem")
        public_pem = public_path.read_bytes() if public_path.exists() else None
        return private_pem, public_pem

    priv_var = os.environ.get("JWT_PRIVATE_KEY", "")
    pub_var = os.environ.get("JWT_PUBLIC_KEY", "")
    if priv_var:
        return priv_var.encode(), pub_var.encode() if pub_var else None

    priv, pub = generate_key_pair()
    return priv, pub
