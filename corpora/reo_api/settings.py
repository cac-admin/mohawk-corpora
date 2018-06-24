
try:
    from .local_settings import *
except ImportError:
    pass

from corpus.base_settings import *
from people.base_settings import *
from corpora.base_settings import *

from transcriptions.base_settings import *

# Site ID for Reo API
SITE_ID = 2
