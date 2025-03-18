import scrapy
import fitz  
import io
import os
import json
import re
from ..items import ArticleItem, SubArticleItem, SectionItem 


# this spider doesn't inherit the basespider
# it uses the items: ArticleItem, SubArticleItem, SectionItem 

class Spider1(scrapy.Spider):
    name = "spider1"
    start_urls = ["https://www.scstatehouse.gov/coderegs/Chapter%2013.pdf"]
    output_dir = "output_data"
    save_path = os.path.join(output_dir, "spider1_chapter_13.json")
    
    def parse(self, response):
       
        pdf_data = io.BytesIO(response.body)
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        extracted_text = "\n".join(page.get_text("text") for page in doc)
       
        structured_data = self.structure_content(extracted_text)

        self.save_output(structured_data)

        for article in structured_data:
            yield article

    def structure_content(self, text):
        """
        Extracts structured content from the PDF text.
        """
        structured_data = []
        current_article = None
        current_subarticle = None
        current_section = None

        # Regex patterns
        article_pattern = re.compile(r"ARTICLE\s+(\d+)")
        subarticle_pattern = re.compile(r"SUBARTICLE\s+(\d+)\s*", re.IGNORECASE)
        section_pattern = re.compile(r"^\d+–(\d+)\.\s+(.*)")

        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Match Articles
            match_article = article_pattern.match(line)
            if match_article:
                if current_article:
                    structured_data.append({"article":dict(current_article)})
                
                i += 1
                title = lines[i].strip() if i < len(lines) else "Unknown Title"
                
                current_article = ArticleItem(
                    num=match_article.group(1),
                    title=title,
                    sections=[],
                    subarticles=[]
                )
                current_subarticle = None
                i += 1
                continue

            # Match Subarticles
            match_subarticle = subarticle_pattern.match(line)
            if match_subarticle and current_article:
                i += 1
                title = lines[i].strip() if i < len(lines) else "Unknown Title"
                
                current_subarticle = SubArticleItem(
                    num=match_subarticle.group(1),
                    title=title,
                    sections=[]
                )
                current_article["subarticles"].append({"subarticle": dict(current_subarticle)})
                i += 1
                continue

            # Match Sections
            match_section = section_pattern.match(line)
            if match_section:
                if current_section:
                    if current_subarticle:
                        current_subarticle["sections"].append({"section":dict(current_section)})
                    else:
                        current_article["sections"].append({"section":dict(current_section)})
                
                current_section = SectionItem(
                    num=match_section.group(1),
                    title=match_section.group(2),
                    content=""
                )
                i += 1
                continue

            # Append content to the current section
            if current_section:
                current_section["content"] += " " + line

            i += 1

        # Save last section & article
        if current_section:
            if current_subarticle:
                current_subarticle["sections"].append({"section":dict(current_section)})
            else:
                current_article["sections"].append({"section":dict(current_section)})

        if current_article:
            structured_data.append({"article":dict(current_article)})

        return structured_data

    def save_output(self, data):
        """
        Saves the structured data to a JSON file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        self.logger.info(f"Saved extracted data to {self.save_path}")


