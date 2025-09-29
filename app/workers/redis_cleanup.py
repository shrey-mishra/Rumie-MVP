"""
Redis cleanup worker for production
Runs periodic cleanup of expired keys to prevent memory leaks
"""

import time
import redis
import os
import structlog
from datetime import datetime

logger = structlog.get_logger("redis_cleanup_worker")

def cleanup_redis_keys():
    """Clean up expired Redis keys"""
    try:
        # Connect to Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        redis_client.ping()
        
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
                   memory_after=memory_after,
                   cleanup_stats=cleanup_stats)
        
        return cleanup_stats
        
    except Exception as e:
        logger.error("Redis cleanup failed", error=str(e))
        return None

def run_cleanup_worker():
    """Run the Redis cleanup worker"""
    logger.info("Redis cleanup worker started")
    
    while True:
        try:
            logger.info("Starting Redis cleanup cycle")
            cleanup_stats = cleanup_redis_keys()
            
            if cleanup_stats:
                logger.info("Cleanup cycle completed successfully",
                           deleted_keys=cleanup_stats["total_deleted"])
            else:
                logger.warning("Cleanup cycle failed")
            
            # Wait 1 hour before next cleanup
            time.sleep(3600)
            
        except KeyboardInterrupt:
            logger.info("Redis cleanup worker stopped by user")
            break
        except Exception as e:
            logger.error("Redis cleanup worker error", error=str(e))
            # Wait 5 minutes before retrying
            time.sleep(300)

if __name__ == "__main__":
    run_cleanup_worker()
