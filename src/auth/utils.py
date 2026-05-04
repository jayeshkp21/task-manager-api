from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from src.config import Config
import logging
import uuid
from itsdangerous import URLSafeTimedSerializer

password_context = CryptContext(schemes=['bcrypt'])

def generate_password_hash(password: str) -> str:
    hash = password_context.hash(password)
    return hash

def verify_password(password: str, hash: str) -> bool:
    return password_context.verify(password, hash)

def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False) -> str:
    payload = {}
    payload['user'] = user_data
    payload['exp'] = datetime.now() + (expiry if expiry else timedelta(seconds=3600))
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = refresh
    
    token = jwt.encode(payload=payload, key=Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    
    return token

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(token, key = Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return token_data
    
    except jwt.PyJWTError as e:
        logging.error(f"Token decoding error: {str(e)}")
        return None
    
serializer = URLSafeTimedSerializer(secret_key=Config.JWT_SECRET, salt='email-configuration')

def create_url_safe_token(data: dict):
    token = serializer.dumps(data)
    return token

def decode_url_safe_token(token: str):
    try:
        token_data = serializer.loads(token)
        return token_data
    
    except Exception as e:
        logging.error(f"URL-safe token decoding error: {str(e)}")
        return None