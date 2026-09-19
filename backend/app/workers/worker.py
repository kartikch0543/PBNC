import asyncio
import logging
from arq.connections import RedisSettings
from app.core.config import settings
from app.workers.tasks import process_document_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup(ctx):
    logger.info("ARQ Document Intelligence Worker started.")


async def shutdown(ctx):
    logger.info("ARQ Document Intelligence Worker shutting down.")


class WorkerSettings:
    functions = [process_document_pipeline]
    redis_settings = RedisSettings.from_dsn(settings.redis_connection_url)
    max_jobs = settings.WORKER_MAX_CONCURRENT_JOBS
    on_startup = startup
    on_shutdown = shutdown


if __name__ == "__main__":
    from arq import run_worker
    run_worker(WorkerSettings)
