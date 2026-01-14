"""
Password hashing and verification using PBKDF2-HMAC-SHA256.
"""
import secrets
import hashlib
import binascii
import sqlite3

from .db import Database


PBKDF2_ITERATIONS = 100_000  # Number of iterations for PBKDF2 hashing


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a random salt.
    Returns a string in format "salt:hash_value"
    """
    # Generate a random 16-byte salt
    salt = secrets.token_bytes(16)

    # Hash the password with the salt, 100,000 iterations
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)

    # Return as a single string: salt(hex) + separator + hash(hex)
    return binascii.hexlify(salt).decode('ascii') + ':' + binascii.hexlify(pwd_hash).decode('ascii')


def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verifies a provided password against the stored hashed password.
    The stored_password is in format "salt:hash_value"
    """
    salt_hex, hash_hex = stored_password.split(':')
    salt = binascii.unhexlify(salt_hex)
    stored_hash = binascii.unhexlify(hash_hex)

    # Hash the provided password with the same salt and iterations
    pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, PBKDF2_ITERATIONS)

    # Compare the hashes
    return pwd_hash == stored_hash


def create_user(db: Database, username: str, password: str) -> bool:
    """
    Creates a new user with hashed password in the database.
    Returns True if successful, False if username already exists.
    """
    hashed_password = hash_password(password)
    try:
        db.execute(
            "INSERT INTO Users (username, password_hash) VALUES (?, ?)",
            (username, hashed_password)
        )
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(db: Database, username: str, password: str) -> int | None:
    """
    Authenticates a user by verifying the provided password.
    Returns True if authentication is successful, False otherwise (user not found or wrong password).
    """
    user = db.select_one(
        "SELECT id, password_hash FROM Users WHERE username = ?",
        (username,)
    )
    if user is None:
        return None  # User not found

    stored_password = user['password_hash']
    ok = verify_password(stored_password, password)

    if ok:
        return user['id']
    else:
        return None
