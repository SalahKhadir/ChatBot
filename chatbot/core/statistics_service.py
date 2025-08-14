from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, case
from .models import ApiUsageStats, SystemErrorLog, RateLimitEvent, PlatformMetrics, User
from .database import get_db
import json
import logging

logger = logging.getLogger(__name__)

class StatisticsService:
    """Service for tracking and retrieving platform statistics."""
    
    @staticmethod
    def log_api_usage(
        db: Session,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        gemini_tokens_used: Optional[int] = None,
        gemini_cost_usd: Optional[str] = None,
        rate_limited: bool = False,
        error_message: Optional[str] = None
    ) -> ApiUsageStats:
        """Log an API usage event."""
        try:
            usage_stat = ApiUsageStats(
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=status_code,
                response_time_ms=response_time_ms,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes,
                gemini_tokens_used=gemini_tokens_used,
                gemini_cost_usd=gemini_cost_usd,
                rate_limited=rate_limited,
                error_message=error_message
            )
            
            db.add(usage_stat)
            db.commit()
            db.refresh(usage_stat)
            
            return usage_stat
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def log_system_error(
        db: Session,
        error_type: str,
        error_message: str,
        endpoint: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        error_code: Optional[str] = None,
        stack_trace: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None
    ) -> SystemErrorLog:
        """Log a system error event."""
        try:
            error_log = SystemErrorLog(
                error_type=error_type,
                endpoint=endpoint,
                user_id=user_id,
                ip_address=ip_address,
                error_code=error_code,
                error_message=error_message,
                stack_trace=stack_trace,
                request_data=json.dumps(request_data) if request_data else None
            )
            
            db.add(error_log)
            db.commit()
            db.refresh(error_log)
            
            return error_log
        except Exception as e:
            logger.error(f"Error logging system error: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def log_rate_limit_event(
        db: Session,
        ip_address: str,
        endpoint: str,
        limit_type: str,
        current_count: int,
        limit_threshold: int,
        user_id: Optional[int] = None,
        reset_time: Optional[datetime] = None,
        user_agent: Optional[str] = None
    ) -> RateLimitEvent:
        """Log a rate limit event."""
        try:
            rate_limit_event = RateLimitEvent(
                ip_address=ip_address,
                user_id=user_id,
                endpoint=endpoint,
                limit_type=limit_type,
                current_count=current_count,
                limit_threshold=limit_threshold,
                reset_time=reset_time,
                user_agent=user_agent
            )
            
            db.add(rate_limit_event)
            db.commit()
            db.refresh(rate_limit_event)
            
            return rate_limit_event
        except Exception as e:
            logger.error(f"Error logging rate limit event: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def update_platform_metric(
        db: Session,
        metric_name: str,
        metric_value: str,
        metric_type: str = "GAUGE",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> PlatformMetrics:
        """Update or create a platform metric."""
        try:
            metric = PlatformMetrics(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_type=metric_type,
                additional_data=json.dumps(additional_data) if additional_data else None
            )
            
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            return metric
        except Exception as e:
            logger.error(f"Error updating platform metric: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_api_usage_stats(
        db: Session,
        hours: int = 24,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get API usage statistics for the specified time period."""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_query = db.query(ApiUsageStats).filter(
                ApiUsageStats.created_at >= since_time
            )
            
            if user_id:
                base_query = base_query.filter(ApiUsageStats.user_id == user_id)
            if endpoint:
                base_query = base_query.filter(ApiUsageStats.endpoint == endpoint)
            
            # Total requests
            total_requests = base_query.count()
            
            # Requests per minute (approximate)
            requests_per_minute = total_requests / (hours * 60) if hours > 0 else 0
            
            # Success rate
            successful_requests = base_query.filter(
                ApiUsageStats.status_code < 400
            ).count()
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Average response time
            avg_response_time = db.query(func.avg(ApiUsageStats.response_time_ms)).filter(
                ApiUsageStats.created_at >= since_time,
                ApiUsageStats.response_time_ms.isnot(None)
            ).scalar() or 0
            
            # Gemini token usage
            total_gemini_tokens = db.query(func.sum(ApiUsageStats.gemini_tokens_used)).filter(
                ApiUsageStats.created_at >= since_time,
                ApiUsageStats.gemini_tokens_used.isnot(None)
            ).scalar() or 0
            
            # Rate limited requests
            rate_limited_requests = base_query.filter(
                ApiUsageStats.rate_limited == True
            ).count()
            
            # Top endpoints
            top_endpoints = db.query(
                ApiUsageStats.endpoint,
                func.count(ApiUsageStats.id).label('count')
            ).filter(
                ApiUsageStats.created_at >= since_time
            ).group_by(ApiUsageStats.endpoint).order_by(desc('count')).limit(10).all()
            
            # Top users by request count
            top_users = db.query(
                ApiUsageStats.user_id,
                User.email,
                func.count(ApiUsageStats.id).label('count')
            ).join(User, ApiUsageStats.user_id == User.id).filter(
                ApiUsageStats.created_at >= since_time,
                ApiUsageStats.user_id.isnot(None)
            ).group_by(ApiUsageStats.user_id, User.email).order_by(desc('count')).limit(10).all()
            
            return {
                "total_requests": total_requests,
                "requests_per_minute": round(requests_per_minute, 2),
                "success_rate": round(success_rate, 2),
                "avg_response_time_ms": round(float(avg_response_time), 2),
                "total_gemini_tokens": int(total_gemini_tokens),
                "rate_limited_requests": rate_limited_requests,
                "top_endpoints": [{"endpoint": ep, "count": count} for ep, count in top_endpoints],
                "top_users": [{"user_id": uid, "email": email, "count": count} for uid, email, count in top_users],
                "time_period_hours": hours
            }
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            raise
    
    @staticmethod
    def get_error_logs(
        db: Session,
        hours: int = 24,
        error_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent system error logs."""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = db.query(SystemErrorLog).filter(
                SystemErrorLog.created_at >= since_time
            )
            
            if error_type:
                query = query.filter(SystemErrorLog.error_type == error_type)
            
            errors = query.order_by(desc(SystemErrorLog.created_at)).limit(limit).all()
            
            return [
                {
                    "id": error.id,
                    "error_type": error.error_type,
                    "endpoint": error.endpoint,
                    "user_id": error.user_id,
                    "user_email": error.user.email if error.user else None,
                    "ip_address": error.ip_address,
                    "error_code": error.error_code,
                    "error_message": error.error_message,
                    "created_at": error.created_at.isoformat() if error.created_at else None
                }
                for error in errors
            ]
        except Exception as e:
            logger.error(f"Error getting error logs: {e}")
            raise
    
    @staticmethod
    def get_rate_limit_dashboard(
        db: Session,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get rate limit dashboard data."""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Total rate limit events
            total_events = db.query(RateLimitEvent).filter(
                RateLimitEvent.created_at >= since_time
            ).count()
            
            # Top IPs hitting rate limits
            top_ips = db.query(
                RateLimitEvent.ip_address,
                func.count(RateLimitEvent.id).label('count')
            ).filter(
                RateLimitEvent.created_at >= since_time
            ).group_by(RateLimitEvent.ip_address).order_by(desc('count')).limit(10).all()
            
            # Rate limit events by type
            events_by_type = db.query(
                RateLimitEvent.limit_type,
                func.count(RateLimitEvent.id).label('count')
            ).filter(
                RateLimitEvent.created_at >= since_time
            ).group_by(RateLimitEvent.limit_type).order_by(desc('count')).all()
            
            # Rate limit events by endpoint
            events_by_endpoint = db.query(
                RateLimitEvent.endpoint,
                func.count(RateLimitEvent.id).label('count')
            ).filter(
                RateLimitEvent.created_at >= since_time
            ).group_by(RateLimitEvent.endpoint).order_by(desc('count')).limit(10).all()
            
            # Recent events
            recent_events = db.query(RateLimitEvent).filter(
                RateLimitEvent.created_at >= since_time
            ).order_by(desc(RateLimitEvent.created_at)).limit(20).all()
            
            return {
                "total_events": total_events,
                "top_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
                "events_by_type": [{"type": t, "count": count} for t, count in events_by_type],
                "events_by_endpoint": [{"endpoint": ep, "count": count} for ep, count in events_by_endpoint],
                "recent_events": [
                    {
                        "id": event.id,
                        "ip_address": event.ip_address,
                        "user_id": event.user_id,
                        "user_email": event.user.email if event.user else None,
                        "endpoint": event.endpoint,
                        "limit_type": event.limit_type,
                        "current_count": event.current_count,
                        "limit_threshold": event.limit_threshold,
                        "created_at": event.created_at.isoformat() if event.created_at else None
                    }
                    for event in recent_events
                ],
                "time_period_hours": hours
            }
        except Exception as e:
            logger.error(f"Error getting rate limit dashboard: {e}")
            raise
    
    @staticmethod
    def get_hourly_request_chart_data(
        db: Session,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get hourly request data for charts."""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get all requests in the time period
            requests = db.query(ApiUsageStats).filter(
                ApiUsageStats.created_at >= since_time
            ).all()
            
            # Group by hour manually
            hourly_stats = {}
            
            for request in requests:
                if request.created_at:
                    # Round down to the hour
                    hour_key = request.created_at.replace(minute=0, second=0, microsecond=0)
                    hour_str = hour_key.strftime('%Y-%m-%d %H:00:00')
                    
                    if hour_str not in hourly_stats:
                        hourly_stats[hour_str] = {
                            'requests': 0,
                            'successful': 0,
                            'rate_limited': 0,
                            'response_times': []
                        }
                    
                    hourly_stats[hour_str]['requests'] += 1
                    
                    if request.status_code and request.status_code < 400:
                        hourly_stats[hour_str]['successful'] += 1
                    
                    if request.rate_limited:
                        hourly_stats[hour_str]['rate_limited'] += 1
                    
                    if request.response_time_ms:
                        hourly_stats[hour_str]['response_times'].append(request.response_time_ms)
            
            # Convert to list format
            result = []
            for hour_str, stats in sorted(hourly_stats.items()):
                avg_response_time = 0
                if stats['response_times']:
                    avg_response_time = sum(stats['response_times']) / len(stats['response_times'])
                
                result.append({
                    "hour": hour_str,
                    "requests": stats['requests'],
                    "successful": stats['successful'],
                    "rate_limited": stats['rate_limited'],
                    "avg_response_time": round(avg_response_time, 2)
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting hourly request chart data: {e}")
            raise

    @staticmethod
    def create_sample_data(db: Session):
        """Create sample statistics data for testing."""
        try:
            from datetime import datetime, timedelta
            import random
            
            # Clear existing data
            db.query(ApiUsageStats).delete()
            db.query(SystemErrorLog).delete()
            db.query(RateLimitEvent).delete()
            
            # Get actual user IDs from the database
            existing_users = db.query(User.id).all()
            existing_user_ids = [user.id for user in existing_users] if existing_users else []
            
            # Generate sample API usage stats for the last 24 hours
            now = datetime.utcnow()
            
            endpoints = ["/chat/public", "/auth/login", "/admin/users", "/documents/upload", "/user/profile"]
            status_codes = [200, 200, 200, 201, 400, 401, 429, 500]  # weighted towards success
            
            for i in range(100):  # Create 100 sample requests
                created_time = now - timedelta(hours=random.randint(0, 24), minutes=random.randint(0, 60))
                endpoint = random.choice(endpoints)
                status = random.choice(status_codes)
                
                # Use actual user ID or None for anonymous requests
                user_id = None
                if existing_user_ids and random.random() > 0.3:  # 70% chance of having a user_id
                    user_id = random.choice(existing_user_ids)
                
                usage_stat = ApiUsageStats(
                    endpoint=endpoint,
                    method="POST" if endpoint in ["/auth/login", "/chat/public"] else "GET",
                    user_id=user_id,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    status_code=status,
                    response_time_ms=random.randint(50, 2000),
                    gemini_tokens_used=random.randint(10, 500) if endpoint == "/chat/public" else None,
                    rate_limited=status == 429,
                    created_at=created_time
                )
                db.add(usage_stat)
            
            # Generate sample error logs
            error_types = ["API_ERROR", "PARSING_ERROR", "AUTH_ERROR", "RATE_LIMIT_ERROR"]
            for i in range(10):
                error_time = now - timedelta(hours=random.randint(0, 24))
                
                # Use actual user ID or None
                user_id = None
                if existing_user_ids and random.random() > 0.5:
                    user_id = random.choice(existing_user_ids)
                
                error_log = SystemErrorLog(
                    error_type=random.choice(error_types),
                    endpoint=random.choice(endpoints),
                    error_message=f"Sample error message {i+1}",
                    user_id=user_id,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    created_at=error_time
                )
                db.add(error_log)
            
            # Generate sample rate limit events
            for i in range(5):
                rate_time = now - timedelta(hours=random.randint(0, 24))
                
                # Use actual user ID or None
                user_id = None
                if existing_user_ids and random.random() > 0.5:
                    user_id = random.choice(existing_user_ids)
                
                rate_event = RateLimitEvent(
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    user_id=user_id,
                    endpoint=random.choice(endpoints),
                    limit_type="REQUEST_LIMIT",
                    current_count=random.randint(100, 150),
                    limit_threshold=100,
                    created_at=rate_time
                )
                db.add(rate_event)
            
            db.commit()
            logger.info("Sample statistics data created successfully")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            db.rollback()
            raise
