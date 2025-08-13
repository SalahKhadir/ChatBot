import time
from collections import defaultdict
from fastapi import Request
from config.settings import MAX_REQUESTS_PER_IP, MAX_FILES_PER_IP, RATE_LIMIT_WINDOW

# In-memory storage for rate limiting (IP -> {requests: count, files: count, reset_time: timestamp})
rate_limit_storage = defaultdict(lambda: {'requests': 0, 'files': 0, 'reset_time': 0})

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Try to get real IP from headers first (for proxy/load balancer setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return "unknown"

def cleanup_expired_entries():
    """Remove expired entries from rate limit storage"""
    current_time = time.time()
    expired_ips = [
        ip for ip, data in rate_limit_storage.items() 
        if current_time > data['reset_time']
    ]
    for ip in expired_ips:
        del rate_limit_storage[ip]

def check_rate_limit(request: Request, limit_type: str) -> dict:
    """
    Check rate limit for IP address
    
    Args:
        request: FastAPI Request object
        limit_type: Either 'request' or 'file'
    
    Returns:
        dict with 'allowed', 'remaining', and 'reset_time' keys
    """
    cleanup_expired_entries()
    
    client_ip = get_client_ip(request)
    current_time = time.time()
    
    # Get or initialize data for this IP
    ip_data = rate_limit_storage[client_ip]
    
    # Reset counters if window has expired
    if current_time > ip_data['reset_time']:
        ip_data['requests'] = 0
        ip_data['files'] = 0
        ip_data['reset_time'] = current_time + RATE_LIMIT_WINDOW
    
    # Check limits based on type
    if limit_type == 'request':
        current_count = ip_data['requests']
        max_limit = MAX_REQUESTS_PER_IP
    elif limit_type == 'file':
        current_count = ip_data['files']
        max_limit = MAX_FILES_PER_IP
    else:
        raise ValueError("limit_type must be 'request' or 'file'")
    
    # Check if limit exceeded
    if current_count >= max_limit:
        return {
            'allowed': False,
            'remaining': 0,
            'reset_time': ip_data['reset_time'],
            'message': f"Rate limit exceeded. Maximum {max_limit} {limit_type}s allowed per 24 hours."
        }
    
    return {
        'allowed': True,
        'remaining': max_limit - current_count,
        'reset_time': ip_data['reset_time'],
        'message': f"{max_limit - current_count} {limit_type}s remaining"
    }

def increment_rate_limit(request: Request, limit_type: str):
    """Increment the rate limit counter for an IP"""
    client_ip = get_client_ip(request)
    if limit_type == 'request':
        rate_limit_storage[client_ip]['requests'] += 1
    elif limit_type == 'file':
        rate_limit_storage[client_ip]['files'] += 1

def increment_file_count(request: Request):
    """Increment file upload count for rate limiting"""
    increment_rate_limit(request, 'file')
