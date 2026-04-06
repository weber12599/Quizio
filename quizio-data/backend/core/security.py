import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

# JWT Configuration settings
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = os.getenv('JWT_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES'))


def get_password_hash(password: str) -> str:
    # Convert string to bytes
    password_bytes = password.encode('utf-8')

    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)

    # Decode back to string for database storage
    return hashed_password_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Convert both strings to bytes
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')

    # Safely verify the password to prevent timing attacks
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(data: dict) -> str:
    """
    Generate a JWT token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})

    # Create the encoded JWT string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_student_upload_token(teacher_id: int, room_pin: str) -> str:
    """
    Generate a temporary JWT token for students to upload media via Tiptap.
    The storage quota and ownership will be attributed to the teacher who created the room.
    """
    # Set expiration for the duration of a typical test session (e.g., 4 hours)
    expire = datetime.now(timezone.utc) + timedelta(hours=4)

    to_encode = {
        'sub': str(teacher_id),
        'scope': 'student_upload',
        'room_pin': room_pin,
        'exp': expire,
    }

    # Create the encoded JWT string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
