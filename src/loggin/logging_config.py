import logging
from colorama import Fore, Style, init


init(autoreset=True) #per evitare problemi su altri OS

class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT
        }.get(record.levelno, '')
        
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

def get_logger(name=None):
    logger = logging.getLogger(name)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter('%(levelname)s | %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    return logger
