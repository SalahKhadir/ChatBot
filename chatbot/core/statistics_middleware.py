from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Callable
from sqlalchemy.orm import Session
from .database import get_db
from .statistics_service import StatisticsService
from .auth import get_current_user_optional
import asyncio

logger = logging.getLogger(__name__)

class StatisticsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track API usage statistics."""
    
    def __init__(self, app, track_all_requests: bool = True):
        super().__init__(app)
        self.track_all_requests = track_all_requests
        
        # Endpoints to exclude from tracking (to avoid infinite loops)
        self.excluded_endpoints = {
            "/docs", "/redoc", "/openapi.json", "/favicon.ico",
            "/static", "/health", "/metrics"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and track statistics."""
        
        # Skip tracking for excluded endpoints
        if any(request.url.path.startswith(excluded) for excluded in self.excluded_endpoints):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request info
        method = request.method
        endpoint = request.url.path
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        # Get request size (approximate)
        request_size_bytes = len(str(request.headers)) + request.headers.get("content-length", 0)
        if isinstance(request_size_bytes, str):
            try:
                request_size_bytes = int(request_size_bytes)
            except:
                request_size_bytes = 0
        
        # Process request
        response = None
        error_message = None
        user_id = None
        
        try:
            # Try to get current user (if authenticated)
            try:
                # This is a simplified approach - in production you'd want to properly handle async auth
                user_id = await self._get_user_id_from_request(request)
            except:
                user_id = None
            
            # Call the actual endpoint
            response = await call_next(request)
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Request failed: {error_message}")
            # Re-raise the exception
            raise
        
        finally:
            # Calculate metrics
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Get response info
            status_code = response.status_code if response else 500
            response_size_bytes = None
            if response and hasattr(response, 'headers'):
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        response_size_bytes = int(content_length)
                    except:
                        pass
            
            # Check if rate limited (based on status code)
            rate_limited = status_code == 429
            
            # Log the usage statistics asynchronously
            asyncio.create_task(self._log_usage_async(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                response_time_ms=response_time_ms,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes,
                rate_limited=rate_limited,
                error_message=error_message
            ))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP first (in case of proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in case of multiple
            return forwarded_for.split(",")[0].strip()
        
        # Check other possible headers
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _get_user_id_from_request(self, request: Request) -> int:
        """Try to extract user ID from the request."""
        # This is a simplified version - you might need to adapt based on your auth implementation
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # You'd implement proper JWT parsing here
                # For now, return None if no simple way to get user
                return None
        except:
            pass
        return None
    
    async def _log_usage_async(self, **kwargs):
        """Log usage statistics asynchronously."""
        try:
            # Get database session
            db = next(get_db())
            
            # Log the usage
            StatisticsService.log_api_usage(db, **kwargs)
            
        except Exception as e:
            logger.error(f"Error logging API usage statistics: {e}")
        finally:
            try:
                db.close()
            except:
                pass

def log_error_async(
    error_type: str,
    error_message: str,
    endpoint: str = None,
    user_id: int = None,
    ip_address: str = None,
    error_code: str = None,
    stack_trace: str = None,
    request_data: dict = None
):
    """Helper function to log errors asynchronously."""
    try:
        db = next(get_db())
        StatisticsService.log_system_error(
            db=db,
            error_type=error_type,
            error_message=error_message,
            endpoint=endpoint,
            user_id=user_id,
            ip_address=ip_address,
            error_code=error_code,
            stack_trace=stack_trace,
            request_data=request_data
        )
    except Exception as e:
        logger.error(f"Error logging system error: {e}")
    finally:
        try:
            db.close()
        except:
            pass

def log_rate_limit_async(
    ip_address: str,
    endpoint: str,
    limit_type: str,
    current_count: int,
    limit_threshold: int,
    user_id: int = None,
    reset_time = None,
    user_agent: str = None
):
    """Helper function to log rate limit events asynchronously."""
    try:
        db = next(get_db())
        StatisticsService.log_rate_limit_event(
            db=db,
            ip_address=ip_address,
            endpoint=endpoint,
            limit_type=limit_type,
            current_count=current_count,
            limit_threshold=limit_threshold,
            user_id=user_id,
            reset_time=reset_time,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error logging rate limit event: {e}")
    finally:
        try:
            db.close()
        except:
            pass
