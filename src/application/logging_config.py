import logging
from colorama import Fore, Style, init, Back


init(autoreset=True) 


# Definizione livello custom
CUSTOM_LEVEL = 25  # tra INFO (20) e WARNING (30)
logging.addLevelName(CUSTOM_LEVEL, "NOTICE")

def notice(self, message, *args, **kwargs):
    if self.isEnabledFor(CUSTOM_LEVEL):
        self._log(CUSTOM_LEVEL, message, args, **kwargs)

logging.Logger.notice = notice  # aggiungiamo il metodo a Logger


class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            CUSTOM_LEVEL: Back.YELLOW + Fore.BLACK,  # nuovo colore
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT
        }.get(record.levelno, '')
        
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"


def setup_logging(level=logging.INFO):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(ColorFormatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))


    if not root_logger.hasHandlers():
        root_logger.addHandler(handler)



