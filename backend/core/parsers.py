from parsers.applegod import AppleGodParser
from parsers.applemarket import AppleMarketParser
from parsers.i_shop import IShopParser
from parsers.macapples import MacApplesParser
from parsers.techmart import TechmartParser

PARSERS = [
    AppleMarketParser(),
    AppleGodParser(),
    IShopParser(),
    MacApplesParser(),
    TechmartParser(),
]
