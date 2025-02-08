import colorlog
import logging

logger = colorlog.getLogger()

handler = colorlog.StreamHandler()

handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d\n%(log_color)s|__%(message_log_color)s%(message)s",
        log_colors={
            "DEBUG": "light_black",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={
            "message": {
                "DEBUG": "light_black",
                "INFO": "white",
                "WARNING": "white",
                "ERROR": "white",
                "CRITICAL": "white",
            }
        },
        style="%",
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
