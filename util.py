import logging

from pathlib import Path

FMT = '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)-3d] %(message)s'
DATEFMT = '%H:%M:%S'

def get_logger(name, dirname='logs'):
    logger = logging.getLogger(name)
    if logger.hasHandlers(): return logger
    # you can change the logging level to DEBUG on the returned obj
    logger.setLevel(logging.INFO)

    if name == 'main':
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
    else:
        dirname = Path(dirname)
        handler = logging.FileHandler(filename=dirname/f'{name}.txt', mode='w')
        handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt=FMT,datefmt=DATEFMT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
