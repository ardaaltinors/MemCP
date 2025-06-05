import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import text
from qdrant_client import QdrantClient
import redis
from src.db.database import engine
from src.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


def check_postgres_health() -> Dict[str, Any]:
    """Check PostgreSQL database health."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        return {
            "status": "healthy",
            "details": "Connection successful"
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": f"Connection failed: {str(e)}"
        }


def check_qdrant_health() -> Dict[str, Any]:
    """Check Qdrant vector database health."""
    try:
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        client.get_collections()
        return {
            "status": "healthy",
            "details": "Connection successful, able to list collections"
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": f"Connection failed: {str(e)}"
        }


def check_redis_health() -> Dict[str, Any]:
    """Check Redis cache health."""
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            socket_connect_timeout=5
        )
        redis_client.ping()
        key_count = redis_client.dbsize()
        return {
            "status": "healthy",
            "details": f"Connection successful, {key_count} keys in DB"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": f"Connection failed: {str(e)}"
        }


def check_rabbitmq_health() -> Dict[str, Any]:
    """Check RabbitMQ broker health via Celery connection."""
    try:
        from src.celery_app import celery_app
        
        # Test broker connection
        broker_connection = celery_app.connection()
        broker_connection.ensure_connection(max_retries=3)
        broker_connection.release()
        
        return {
            "status": "healthy",
            "details": "Broker connection successful"
        }
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": f"Broker connection failed: {str(e)}"
        }


def check_celery_workers_health() -> Dict[str, Any]:
    """Check Celery workers health."""
    try:
        from src.celery_app import celery_app
        
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if active_workers:
            worker_list = []
            for worker_name in active_workers.keys():
                worker_info = {
                    "name": worker_name,
                    "active_tasks": len(active_workers.get(worker_name, [])),
                    "status": "online"
                }
                if stats and worker_name in stats:
                    worker_info["pool"] = stats[worker_name].get("pool", {}).get("implementation", "unknown")
                worker_list.append(worker_info)
            
            return {
                "status": "healthy",
                "details": f"{len(worker_list)} worker(s) online",
                "workers": worker_list
            }
        else:
            return {
                "status": "unhealthy",
                "details": "No active workers found",
                "workers": []
            }
    except Exception as e:
        logger.error(f"Celery workers health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": f"Worker inspection failed: {str(e)}",
            "workers": []
        }


def determine_overall_status(services: Dict[str, Dict[str, Any]]) -> str:
    """
    Determine overall application health status based on service health.
    
    Args:
        services: Dictionary of service health statuses
        
    Returns:
        Overall status: "healthy", "degraded", or "unhealthy"
        
    Raises:
        ServiceUnavailableError: If multiple critical services are down
    """
    critical_services = ["postgres", "qdrant", "rabbitmq", "redis"]
    unhealthy_critical = [
        svc for svc in critical_services 
        if services[svc]["status"] == "unhealthy"
    ]
    
    if len(unhealthy_critical) >= 2:
        raise ServiceUnavailableError(
            message=f"Multiple critical services unavailable: {', '.join(unhealthy_critical)}",
            service_name=",".join(unhealthy_critical)
        )
    elif len(unhealthy_critical) == 1:
        return "degraded"
    else:
        # Check if any non-critical services are down
        all_unhealthy = [
            svc for svc, details in services.items() 
            if details["status"] == "unhealthy"
        ]
        return "degraded" if all_unhealthy else "healthy"


def perform_full_health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check of all services.
    
    Returns:
        Complete health status including individual service statuses and overall health
    """
    status = {
        "status": "healthy",
        "services": {
            "postgres": {"status": "unknown", "details": ""},
            "qdrant": {"status": "unknown", "details": ""},
            "rabbitmq": {"status": "unknown", "details": ""},
            "redis": {"status": "unknown", "details": ""},
            "celery": {"status": "unknown", "details": "", "workers": []}
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Check each service
    status["services"]["postgres"] = check_postgres_health()
    status["services"]["qdrant"] = check_qdrant_health()
    status["services"]["rabbitmq"] = check_rabbitmq_health()
    status["services"]["redis"] = check_redis_health()
    status["services"]["celery"] = check_celery_workers_health()
    
    # Determine overall status
    status["status"] = determine_overall_status(status["services"])
    
    return status 