import logging
from django.utils import timezone
from django.core.signals import request_started, request_finished
from django.db.backends.signals import connection_created
from celery.signals import task_prerun, task_postrun, task_failure

LOG_FILE = "coinlytics_system.log"


# Configuring root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Creating a file handler for app-wide logging
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# ✅ Registering request lifecycle signals (logs every web and API requests)
def log_request_started(sender, environ, **kwargs):
    logger.info("Request started: %s %s", environ.get(
        "REQUEST_METHOD"), environ.get("PATH_INFO"))


def log_request_completed(sender, **kwargs):
    logger.info("Request completed successfully")


request_started.connect(log_request_started)
request_finished.connect(log_request_completed)


# ✅ Logging database connection
def log_db_connection(sender, connection, **kwargs):
    logger.info("Database connected: %s", connection.settings_dict.get("NAME"))


connection_created.connect(log_db_connection)


# ✅ Celery task lifecycle signals
# BUG FIX: The README documents task_prerun, task_postrun, and task_failure
# log entries, but none of these signals were actually connected. Without them,
# the log file had no record of whether background tasks ran or failed —
# making the "Automated Logging System" silent for all Celery activity.
# Celery emits these signals on every worker task execution, so connecting
# them here (at import time, via settings.py → core.logging_config) ensures
# they fire for every task across all apps without modifying each task file.

def log_task_started(sender, task_id, task, args, kwargs, **extra):
    logger.info("🚀 Celery Task Started: %s [id=%s]", sender, task_id)


def log_task_completed(sender, task_id, task, args, kwargs, retval, **extra):
    logger.info("✅ Celery Task Completed: %s [id=%s]", sender, task_id)


def log_task_failed(sender, task_id, exception, traceback, **extra):
    # Log at ERROR level so failures are distinguishable from normal INFO
    # entries and can be filtered easily in log analysis tools.
    logger.error(
        "❌ Celery Task Failed: %s [id=%s] — %s",
        sender, task_id, exception
    )


task_prerun.connect(log_task_started)
task_postrun.connect(log_task_completed)
task_failure.connect(log_task_failed)


logger.info("🟢 Logging system initialized at %s", timezone.now())
