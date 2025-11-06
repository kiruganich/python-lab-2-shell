import logging
import os

def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/shell.log",
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger("MiniShell")