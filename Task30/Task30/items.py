# Define here the models for your scraped items

# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
########## these following items are used in spider1
# each section is defined by number, title and content
class SectionItem(scrapy.Item):
    num = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()

# each subarticle has number, title and many sections
class SubArticleItem(scrapy.Item):
    num = scrapy.Field()
    title = scrapy.Field()
    sections = scrapy.Field()  # List of SectionItem

# each article number, title and may have many subarticles or many sections
class ArticleItem(scrapy.Item):
    num = scrapy.Field()
    title = scrapy.Field()
    sections = scrapy.Field()  # List of SectionItem
    subarticles = scrapy.Field()  # List of SubArticleItem

##################
#used in spider2
class SrcaItem(scrapy.Item):
    title = scrapy.Field()
    text = scrapy.Field()
    meta_data = scrapy.Field()
    html_body = scrapy.Field()
    