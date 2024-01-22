import logging

from typing import Tuple


class Logger:
    def init(self, log_path: str) -> None:
        fmt = "%(asctime)s - [%(levelname)s]%(message)s"
        logging.basicConfig(
            filename=log_path,
            format=fmt,
            datefmt="%m/%d/%Y %I:%M:%S %p",
            encoding="utf-8",
            level=logging.DEBUG,
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(fmt))
        logging.getLogger().addHandler(console_handler)

    def set_level(self, level: int = logging.DEBUG) -> None:
        logging.getLogger().setLevel(level)

    def debug(self, text: str, *args: Tuple) -> None:
        text = "    \t" + text % args
        logging.debug(text)

    def info(self, text: str, *args: Tuple) -> None:
        logging.info(text % args)

    def warning(self, text: str, *args: Tuple) -> None:
        logging.warning(text % args)

    def error(self, text: str, *args: Tuple) -> None:
        logging.error(text % args)

    def show(self, text: str, *args: Tuple) -> None:
        logging.info(text % args)


logger = Logger()
