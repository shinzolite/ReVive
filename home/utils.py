from django.conf import settings
import hashlib
import hmac

def generate_chat_hash(buy_request_id):
    """Generate a secure hash for the chat URL"""
    key = settings.SECRET_KEY.encode()
    message = f"chat_{buy_request_id}".encode()
    hash_obj = hmac.new(key, message, hashlib.sha256)
    return hash_obj.hexdigest()[:16]  # Using first 16 chars for shorter URL

def verify_chat_hash(hash_value, buy_request_id):
    """Verify if a hash matches a buy request ID"""
    expected_hash = generate_chat_hash(buy_request_id)
    return hmac.compare_digest(hash_value, expected_hash) 