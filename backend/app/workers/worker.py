import asyncio
import logging
import sys
import redis.asyncio as aioredis
from arq import run_worker
from arq.connections import RedisSettings
from app.core.config import settings
from app.workers.tasks import process_document_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("document_intelligence_worker")


async def verify_redis_connection() -> bool:
    """Verifies whether a Redis daemon is reachable before booting worker."""
    try:
        client = aioredis.from_url(settings.redis_connection_url, socket_connect_timeout=1.5)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


async def startup(ctx):
    logger.info("ARQ Document Intelligence Worker process started successfully.")


async def shutdown(ctx):
    logger.info("ARQ Document Intelligence Worker process shutting down.")


class WorkerSettings:
    functions = [process_document_pipeline]
    redis_settings = RedisSettings.from_dsn(settings.redis_connection_url)
    max_jobs = settings.WORKER_MAX_CONCURRENT_JOBS
    on_startup = startup
    on_shutdown = shutdown


if __name__ == "__main__":
    is_reachable = asyncio.run(verify_redis_connection())
    if not is_reachable:
        print("\n" + "=" * 75)
        print(f" NOTICE: Redis server is not currently reachable at {settings.REDIS_HOST}:{settings.REDIS_PORT}.")
        print(" The Document Intelligence API already handles background processing tasks")
        print(" automatically in-process via FastAPI without requiring an external Redis broker.")
        print(" To run this dedicated ARQ multi-process worker, launch Redis locally on port 6379.")
        print("=" * 75 + "\n")
        sys.exit(0)

    run_worker(WorkerSettings)
