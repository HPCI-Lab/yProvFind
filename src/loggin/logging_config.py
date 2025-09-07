import logging
from colorama import Fore, Style, init

# i loggher hanno una gerarchia ad albero, ad esempio il logger del file src/routers/root.py ha come nome "src.routers.root", il padre di questo logger e' "src.routers" e il padre di questo e' "src".
# l'idea dei logger è avere un sistema centralizzato per la gestione dei log, in modo che ogni modulo o componente dell'applicazione possa avere il proprio logger con una configurazione specifica, ma che erediti alcune impostazioni comuni dal logger principale.
# si possono anche rendere indipendenti scrivendo in get_logger logger.propagate = False
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



def setup_logging(level= logging.INFO):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler=logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(ColorFormatter('%(levelname)s | %(message)s'))

    if not root_logger.hasHandlers():
        root_logger.addHandler(handler)





""""" #Questo pezzo di codice serve per configurare il logging indipendente per ogni modulo e non centralizzato
def get_logger(name=None):
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter('%(levelname)s | %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    return logger
"""