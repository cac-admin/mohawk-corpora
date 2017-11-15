from .base_settings import *

try:
    from .local_settings import *
except ImportError:
    pass


from corpus.base_settings import *
from people.base_settings import *