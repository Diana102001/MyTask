from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from .items import SectionItem, SubArticleItem, ArticleItem, SrcaItem

def clean_text(text):
    return text.strip() if text else text

class SectionLoader(ItemLoader):
    default_item_class = SectionItem
    default_output_processor = TakeFirst()
    num_in = MapCompose(str.strip)
    title_in = MapCompose(clean_text)
    content_in = MapCompose(str.strip)  # Or any other processing you want


class SubArticleLoader(ItemLoader):
    default_item_class = SubArticleItem
    default_output_processor = TakeFirst()
    num_in = MapCompose(str.strip)
    title_in = MapCompose(clean_text)
    sections_in = MapCompose(SectionLoader.load_item)

class ArticleLoader(ItemLoader):
    default_item_class = ArticleItem
    default_output_processor = TakeFirst()
    num_in = MapCompose(str.strip)
    title_in = MapCompose(clean_text)
    sections_in = MapCompose(SectionLoader.load_item)
    subarticles_in = MapCompose(SubArticleLoader.load_item)

class SrcaItemLoader(ItemLoader):
    default_item_class = SrcaItem
    title_in = MapCompose(str.strip)
