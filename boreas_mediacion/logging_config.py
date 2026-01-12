# Logging configuration for Boreas Mediacion
# Import this in settings.py to suppress verbose MQTT messages

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'paho.mqtt': {
            'handlers': ['console'],
            'level': 'ERROR',  # Solo errores de MQTT
            'propagate': False,
        },
        'paho.mqtt.client': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'boreas_mediacion': {
            'handlers': ['console'],
            'level': 'WARNING',  # Suppress debug/info messages like "Reported measure updated"
            'propagate': False,
        },
    },
}
