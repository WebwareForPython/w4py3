# URL/test1

import os

from URLParser import URLParameterParser, FileParser

urlParser = URLParameterParser(FileParser(os.path.dirname(__file__)))
