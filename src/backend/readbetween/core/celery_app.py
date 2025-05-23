from celery import Celery
from readbetween.config import settings

celery_broker = f"{settings.storage.redis.uri}/11"
celery_backend = f"{settings.storage.redis.uri}/12"


def make_celery(app_name='ywjz-celery-tasks',
                broker=celery_broker,
                backend=celery_backend):
    celery = Celery(app_name, broker=broker, backend=backend)
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],  # 只接受 JSON 格式的内容
        result_serializer='json',  # 任务结果序列化格式为 JSON
        timezone='Asia/Shanghai',  # 设置时区为上海
        enable_utc=False,  # 不使用 UTC 时间，因为已经设置了具体的时区
    )
    celery.autodiscover_tasks(['readbetween.services.tasks'])
    return celery


celery = make_celery()
