from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from io import BufferedWriter
import json
from logging import getLogger

from sqlitelib.utils.common import get_exception_detail

logger = getLogger()

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, BufferedWriter):
            return '(BufferWriter object)'
        elif hasattr(o, '__dataclass_fields__'):
            return asdict(o)
        
        try:
            return super().default(o)
        except TypeError as te:
            try:
                return str(o)
            except Exception as e:
                logger.error(get_exception_detail(te))
                logger.error(get_exception_detail(e))
                return "Unsupported Type"