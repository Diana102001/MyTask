# # Define here the models for your scraped items
# #
# # See documentation in:
# # https://docs.scrapy.org/en/latest/topics/items.html

# import scrapy


# class Task30Item(scrapy.Item):
#     # define the fields for your item here like:
#     # name = scrapy.Field()
#     pass

# class Article(scrapy.Item):
#     num=scrapy.Field()
#     name=scrapy.Field()
# class SubArticle(scrapy.Item):
#     num=scrapy.Field()
#     name=scrapy.Field()
# class Section(scrapy.Item):
#     num=scrapy.Field()
#     name=scrapy.Field()
#     content=scrapy.Field()


import scrapy

class SectionItem(scrapy.Item):
    num = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()

class SubArticleItem(scrapy.Item):
    num = scrapy.Field()
    title = scrapy.Field()
    sections = scrapy.Field()  # List of SectionItem

class ArticleItem(scrapy.Item):
    num = scrapy.Field()
    title = scrapy.Field()
    sections = scrapy.Field()  # List of SectionItem
    subarticles = scrapy.Field()  # List of SubArticleItem
class SrcaItem(scrapy.Item):
    title = scrapy.Field()
    text = scrapy.Field()
    meta_data = scrapy.Field()
    html_body = scrapy.Field()
    