import logging

FORMAT = "%(asctime)s - %(levelname)s - %(threadName)s - %(funcName)s():\t %(message)s"
logging.basicConfig(level=logging.DEBUG, filename="log", format=FORMAT)
LOG = logging
