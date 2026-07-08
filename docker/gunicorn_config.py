# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file
# https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing

import structlog

bind = '0.0.0.0:8000'
# Concerning `workers` setting see:
# https://github.com/wemake-services/wemake-django-template/issues/1022
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)

max_requests = 2000
max_requests_jitter = 400

chdir = '/code'
worker_tmp_dir = '/dev/shm'  # noqa: S108

accesslog = '-'
access_log_format = (
    '{"time": "%(t)s", "level": "INFO", "event": "http_request", '
    '"remote_ip": "%(h)s", "method": "%(m)s", "path": "%(U)s", '
    '"query": "%(q)s", "status": %(s)s, "bytes": %(B)s, "time_taken": %(L)s, '
    '"user_agent": "%(a)s"}'
)

logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'gunicorn_access': {
            'format': '%(message)s',
        },
        'gunicorn_error': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
            'foreign_pre_chain': [
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt='iso'),
            ],
        },
    },
    'handlers': {
        'console_access': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'gunicorn_access',
        },
        'console_error': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'gunicorn_error',
        },
    },
    'loggers': {
        'gunicorn.access': {
            'handlers': ['console_access'],
            'level': 'INFO',
            'propagate': False,
        },
        'gunicorn.error': {
            'handlers': ['console_error'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console_error'],
    },
}
