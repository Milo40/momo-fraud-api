import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


class DailyRotatingFileHandler(TimedRotatingFileHandler):
    """Custom handler to add a different date format after the original name."""

    def __init__(
        self,
        filename,
        when="s",
        backupCount=0,
        interval=1,
        encoding=None,
        delay=False,
        utc=True,
    ):
        super().__init__(
            filename,
            when,
            interval,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
            utc=utc,
        )

    def rotate(self, source, dest):
        """
        Override rotate method to append a custom date format to rotated log files.
        """
        base, ext = os.path.splitext(dest)
        ext = ext.replace(".", "")
        # date_f=datetime.strptime(ext.split("_")[0],'%y-%m-%d')
        dest = f"{base}_{ext}"
        super().rotate(source, dest)
