from celery import Celery

from app.core.config import Settings

settings = Settings()

celery_app = Celery(
    "pdf_ai_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="pdf_processing",
    task_default_retry_delay=60,
    task_routes={
        "app.workers.pdf_processor.process_document": {"queue": "pdf_processing"},
        "app.workers.celery_beat.cleanup_old_files": {"queue": "pdf_processing"},
    },
    task_queues=[
        {
            "name": "pdf_processing",
            "exchange": "pdf_processing",
            "routing_key": "pdf_processing",
        },
        {
            "name": "ocr",
            "exchange": "ocr",
            "routing_key": "ocr",
        },
        {
            "name": "ai_formatting",
            "exchange": "ai_formatting",
            "routing_key": "ai_formatting",
        },
    ],
    beat_schedule={
        "cleanup-old-files": {
            "task": "app.workers.celery_beat.cleanup_old_files",
            "schedule": 86400,
        },
    },
    imports=["app.workers.pdf_processor", "app.workers.celery_beat"],
)
