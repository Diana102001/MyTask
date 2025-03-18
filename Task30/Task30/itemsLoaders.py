from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose,Join
from .items import SectionItem, SubArticleItem, ArticleItem, SrcaItem

from scrapy.loader import ItemLoader
import re

# def clean_text(text):
#     return re.sub(r"\s+", " ", text).strip()

# class ArticleLoader(ItemLoader):
#     default_output_processor = TakeFirst()  # Take first value by default
#     title_in = MapCompose(str.strip, clean_text)
#     num_in = MapCompose(str.strip)

# class SubArticleLoader(ItemLoader):
#     default_output_processor = TakeFirst()
#     title_in = MapCompose(str.strip, clean_text)
#     num_in = MapCompose(str.strip)

# class SectionLoader(ItemLoader):
#     default_output_processor = TakeFirst()
#     title_in = MapCompose(str.strip, clean_text)
#     num_in = MapCompose(str.strip)
#     content_in = MapCompose(str.strip)
#     content_out = Join(" ")  # Join multiple content lines into a single paragraph

class SrcaItemLoader(ItemLoader):
    default_item_class = SrcaItem
    title_in = MapCompose(str.strip)
