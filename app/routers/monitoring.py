from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_redis
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any
import json
import time

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("monitoring_router")

@router.get("/redis-stats")
@limiter.limit("30/minute")
async def get_redis_stats(
    request: Request,
    redis_client = Depends(get_redis)
):
    """Get Redis memory and performance statistics"""
    logger.info("Redis stats requested", client_ip=get_remote_address(request))
    
    try:
        # Get Redis info
        info = redis_client.info()
        
        # Extract key metrics
        memory_stats = {
            "used_memory": info.get("used_memory_human", "0B"),
            "used_memory_peak": info.get("used_memory_peak_human", "0B"),
            "max_memory": info.get("maxmemory_human", "0B"),
            "memory_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0)
        }
        
        # Calculate hit rate
        hits = memory_stats["keyspace_hits"]
        misses = memory_stats["keyspace_misses"]
        total_requests = hits + misses
        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
        
        # Get key count by pattern
        key_patterns = {
            "chat_sessions": len(redis_client.keys("chat:*")),
            "user_sessions": len(redis_client.keys("user:*")),
            "total_keys": redis_client.dbsize()
        }
        
        logger.info("Redis stats retrieved", 
                   used_memory=memory_stats["used_memory"],
                   total_keys=key_patterns["total_keys"])
        
        return {
            "status": "healthy",
            "memory": memory_stats,
            "keys": key_patterns,
            "performance": {
                "hit_rate_percentage": round(hit_rate, 2),
                "connected_clients": memory_stats["connected_clients"]
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Redis stats failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis monitoring failed: {str(e)}"
        )

@router.get("/system-health")
@limiter.limit("30/minute")
async def get_system_health(
    request: Request,
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get comprehensive system health status"""
    logger.info("System health check requested", client_ip=get_remote_address(request))
    
    health_status = {
        "overall": "healthy",
        "services": {},
        "timestamp": time.time()
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    # Check Redis
    try:
        start_time = time.time()
        redis_client.ping()
        response_time = (time.time() - start_time) * 1000
        
        # Get Redis memory usage
        redis_info = redis_client.info("memory")
        memory_usage = redis_info.get("used_memory", 0)
        max_memory = redis_info.get("maxmemory", 0)
        memory_percentage = (memory_usage / max_memory * 100) if max_memory > 0 else 0
        
        health_status["services"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "memory_usage_percentage": round(memory_percentage, 2),
            "connected_clients": redis_info.get("connected_clients", 0)
        }
        
        # Alert if memory usage is high
        if memory_percentage > 80:
            health_status["overall"] = "warning"
            health_status["services"]["redis"]["status"] = "warning"
            health_status["services"]["redis"]["alert"] = "High memory usage detected"
            
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    # Check Gemini API (mock for now)
    try:
        from app.services.gemini_service import gemini_service
        # Simple ping test
        test_response = await gemini_service.generate_empathetic_response(
            user_input="Health check ping",
            user_personality="efficient_organizer",
            mode_pref="work"
        )
        
        health_status["services"]["gemini"] = {
            "status": "healthy",
            "confidence": test_response.get("confidence", 0)
        }
    except Exception as e:
        health_status["services"]["gemini"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    # Determine overall status
    unhealthy_services = [s for s in health_status["services"].values() 
                         if s["status"] == "unhealthy"]
    
    if unhealthy_services:
        health_status["overall"] = "unhealthy"
    elif any(s["status"] == "warning" for s in health_status["services"].values()):
        health_status["overall"] = "warning"
    
    logger.info("System health check completed", 
               overall_status=health_status["overall"],
               services_count=len(health_status["services"]))
    
    return health_status

@router.get("/performance-metrics")
@limiter.limit("10/minute")
async def get_performance_metrics(
    request: Request,
    redis_client = Depends(get_redis)
):
    """Get performance metrics for monitoring"""
    logger.info("Performance metrics requested", client_ip=get_remote_address(request))
    
    try:
        # Get Redis performance data
        info = redis_client.info()
        
        # Calculate performance metrics
        uptime_seconds = info.get("uptime_in_seconds", 0)
        total_commands = info.get("total_commands_processed", 0)
        commands_per_second = total_commands / uptime_seconds if uptime_seconds > 0 else 0
        
        # Memory efficiency
        used_memory = info.get("used_memory", 0)
        max_memory = info.get("maxmemory", 0)
        memory_efficiency = (used_memory / max_memory * 100) if max_memory > 0 else 0
        
        # Key statistics
        total_keys = redis_client.dbsize()
        expired_keys = len(redis_client.keys("*"))
        
        metrics = {
            "redis_performance": {
                "commands_per_second": round(commands_per_second, 2),
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "total_commands": total_commands,
                "memory_efficiency_percentage": round(memory_efficiency, 2)
            },
            "key_statistics": {
                "total_keys": total_keys,
                "chat_sessions": len(redis_client.keys("chat:*")),
                "user_sessions": len(redis_client.keys("user:*")),
                "expired_keys": expired_keys
            },
            "recommendations": []
        }
        
        # Add recommendations based on metrics
        if memory_efficiency > 80:
            metrics["recommendations"].append("Consider increasing Redis memory limit")
        
        if commands_per_second > 1000:
            metrics["recommendations"].append("High command rate detected - monitor for performance")
        
        if total_keys > 10000:
            metrics["recommendations"].append("Large number of keys - consider cleanup strategy")
        
        logger.info("Performance metrics calculated", 
                   commands_per_second=commands_per_second,
                   memory_efficiency=memory_efficiency)
        
        return metrics
        
    except Exception as e:
        logger.error("Performance metrics failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Performance monitoring failed: {str(e)}"
        )

@router.post("/redis-cleanup")
@limiter.limit("5/minute")
async def cleanup_redis(
    request: Request,
    redis_client = Depends(get_redis)
):
    """Clean up expired Redis keys to prevent memory leaks"""
    logger.info("Redis cleanup requested", client_ip=get_remote_address(request))
    
    try:
        # Get all keys with patterns
        chat_keys = redis_client.keys("chat:*")
        user_keys = redis_client.keys("user:*")
        blacklist_keys = redis_client.keys("blacklist:*")
        
        deleted_count = 0
        cleanup_stats = {
            "chat_sessions": 0,
            "user_sessions": 0,
            "blacklisted_tokens": 0,
            "total_deleted": 0
        }
        
        # Clean up expired chat sessions
        for key in chat_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:  # Expired or no TTL
                redis_client.delete(key)
                deleted_count += 1
                cleanup_stats["chat_sessions"] += 1
        
        # Clean up expired user sessions
        for key in user_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:  # Expired or no TTL
                redis_client.delete(key)
                deleted_count += 1
                cleanup_stats["user_sessions"] += 1
        
        # Clean up expired blacklisted tokens
        for key in blacklist_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:  # Expired or no TTL
                redis_client.delete(key)
                deleted_count += 1
                cleanup_stats["blacklisted_tokens"] += 1
        
        cleanup_stats["total_deleted"] = deleted_count
        
        # Get Redis memory info after cleanup
        redis_info = redis_client.info("memory")
        memory_after = redis_info.get("used_memory_human", "0B")
        
        logger.info("Redis cleanup completed", 
                   deleted_keys=deleted_count,
                   memory_after=memory_after)
        
        return {
            "status": "cleanup_completed",
            "deleted_keys": deleted_count,
            "cleanup_stats": cleanup_stats,
            "memory_after_cleanup": memory_after,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Redis cleanup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis cleanup failed: {str(e)}"
        )

@router.get("/redis-optimization")
@limiter.limit("10/minute")
async def get_redis_optimization(
    request: Request,
    redis_client = Depends(get_redis)
):
    """Get Redis optimization recommendations"""
    logger.info("Redis optimization analysis requested", client_ip=get_remote_address(request))
    
    try:
        # Get Redis info
        info = redis_client.info()
        memory_info = redis_client.info("memory")
        
        # Analyze key patterns
        all_keys = redis_client.keys("*")
        key_patterns = {}
        for key in all_keys:
            pattern = key.split(":")[0] if ":" in key else "other"
            key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
        
        # Calculate memory efficiency
        used_memory = memory_info.get("used_memory", 0)
        max_memory = memory_info.get("maxmemory", 0)
        memory_efficiency = (used_memory / max_memory * 100) if max_memory > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if memory_efficiency > 80:
            recommendations.append("High memory usage detected - consider increasing Redis memory limit")
        
        if key_patterns.get("chat", 0) > 1000:
            recommendations.append("Large number of chat sessions - consider implementing session cleanup")
        
        if key_patterns.get("blacklist", 0) > 500:
            recommendations.append("Many blacklisted tokens - consider implementing token cleanup")
        
        if len(all_keys) > 10000:
            recommendations.append("Large number of keys - consider implementing key expiration strategy")
        
        # Check for keys without TTL
        keys_without_ttl = 0
        for key in all_keys[:100]:  # Sample first 100 keys
            if redis_client.ttl(key) == -1:  # No expiration set
                keys_without_ttl += 1
        
        if keys_without_ttl > 50:
            recommendations.append("Many keys without TTL - consider setting expiration times")
        
        optimization_data = {
            "memory_efficiency": round(memory_efficiency, 2),
            "total_keys": len(all_keys),
            "key_patterns": key_patterns,
            "keys_without_ttl": keys_without_ttl,
            "recommendations": recommendations,
            "memory_usage": memory_info.get("used_memory_human", "0B"),
            "max_memory": memory_info.get("maxmemory_human", "0B")
        }
        
        logger.info("Redis optimization analysis completed", 
                   total_keys=len(all_keys),
                   recommendations_count=len(recommendations))
        
        return optimization_data
        
    except Exception as e:
        logger.error("Redis optimization analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis optimization analysis failed: {str(e)}"
        )
