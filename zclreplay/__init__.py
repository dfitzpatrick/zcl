from .parser import Replay, NotZCReplay, IncompleteReplay, ReplayParseError
from .serializer import ReplayObjectEncoder
from .objects import *
import logging

logging.basicConfig(
    level=logging.CRITICAL,
    format='%(name)-12s: %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
)