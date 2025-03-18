# import scrapy
# import fitz  # PyMuPDF
# import io
# import os
# import json
# import re
# from ..items import ArticleItem, SubArticleItem, SectionItem  # Import Scrapy items

# class SCPDFSpider(scrapy.Spider):
#     name = "sc_pdf_spider"
#     start_urls = ["https://www.scstatehouse.gov/coderegs/Chapter%2013.pdf"]
#     output_dir = "output_data"
#     save_path = os.path.join(output_dir, "sc_chapter_13.json")
    
#     def parse(self, response):
#         """
#         Parses the response, extracts text, and structures the content.
#         """
#         print("\n[INFO] Loading PDF from response...")
#         pdf_data = io.BytesIO(response.body)
#         doc = fitz.open(stream=pdf_data, filetype="pdf")

#         print("\n[INFO] Extracting text from PDF pages...")
#         extracted_text = "\n".join(page.get_text("text") for page in doc)
#         print(f"\n[DEBUG] First 1000 chars of extracted text:\n{extracted_text[:1000]}")  # Debugging output

#         print("\n[INFO] Processing structured content...")
#         structured_data = self.structure_content(extracted_text)

#         print("\n[INFO] Saving extracted data...")
#         self.save_output(structured_data)

#         print("\n[INFO] Yielding extracted items...")
#         for article in structured_data:
#             yield article

#     def structure_content(self, text):
#         """
#         Extracts structured content from the PDF text.
#         """
#         articles = []

#         current_article = None
#         current_subarticle = None
#         current_section = None

#         # Regex patterns
#         article_pattern = re.compile(r"^(ARTICLE)\s+(\d+)\s*$")
#         subarticle_pattern = re.compile(r"^SUBARTICLE\s+(\d+)\s+(.*)", re.IGNORECASE)
#         section_pattern = re.compile(r"^13–(\d+)\.\s+(.*)")

#         lines = text.split("\n")
#         i = 0

#         while i < len(lines):
#             line = lines[i].strip()
#             if not line:
#                 i += 1
#                 continue

#             # Match Articles (capitalized ARTICLE followed by number)
#             match_article = article_pattern.match(line)
#             if match_article:
#                 if current_article:
#                     articles.append(current_article)

#                 # Move to the next line to get the title
#                 i += 1
#                 if i < len(lines):
#                     title = lines[i].strip()
#                 else:
#                     title = "Unknown Title"

#                 print(f"\n[INFO] Found ARTICLE: {match_article.group(2)} - {title}")

#                 current_article = ArticleItem(
#                     num=match_article.group(2),
#                     title=title,
#                     sections=[],
#                     subarticles=[]
#                 )
#                 current_subarticle = None
#                 i += 1
#                 continue

#             # Match Subarticles
#             match_subarticle = subarticle_pattern.match(line)
#             if match_subarticle and current_article:
#                 print(f"\n[INFO] Found SUBARTICLE: {match_subarticle.group(1)} - {match_subarticle.group(2)}")

#                 current_subarticle = SubArticleItem(
#                     num=match_subarticle.group(1),
#                     title=match_subarticle.group(2),
#                     sections=[]
#                 )
#                 current_article["subarticles"].append(current_subarticle)
#                 i += 1
#                 continue

#             # Match Sections (Starts with "13_x")
#             match_section = section_pattern.match(line)
#             if match_section:
#                 if current_section and current_subarticle:
#                     current_subarticle["sections"].append(current_section)
#                 elif current_section and current_article:
#                     current_article["sections"].append(current_section)

#                 print(f"\n[INFO] Found SECTION: {match_section.group(1)} - {match_section.group(2)}")

#                 current_section = SectionItem(
#                     num=match_section.group(1),
#                     title=match_section.group(2),
#                     content=""
#                 )
#                 i += 1
#                 continue
            
#             # Append content to the current section
#             if current_section:
#                 current_section["content"] += " " + line

#         # Append last section, subarticle, and article
#         if current_section and current_subarticle:
#             current_subarticle["sections"].append(current_section)
#         elif current_section and current_article:
#             current_article["sections"].append(current_section)

#         if current_article:
#             articles.append(current_article)

#         return articles

#     def save_output(self, data):
#         """
#         Saves the structured data to a JSON file.
#         """
#         os.makedirs(self.output_dir, exist_ok=True)
#         with open(self.save_path, 'w', encoding='utf-8') as f:
#             json.dump([dict(item) for item in data], f, indent=4, ensure_ascii=False)

#         print(f"\n[SUCCESS] Saved extracted data to {self.save_path}")

import scrapy
import fitz  # PyMuPDF
import io
import os
import json
import re
from datetime import datetime
from ..items import ArticleItem, SectionItem, SubArticleItem,SrcaItem
from ..itemsLoaders import ArticleLoader, SectionLoader, SubArticleLoader ,SrcaItemLoader
import os, json, hashlib

class SCPDFSpider(scrapy.Spider):
    name = "sc_pdf_spider"
    start_urls = ["https://www.scstatehouse.gov/coderegs/Chapter%2013.pdf"]
    output_dir = "output_data"
    save_path = os.path.join(output_dir, "sc_chapter_13.json")
    base_path=f"output_data/{name}/"
    def parse(self, response, doc_types=None):
        
        scraping_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scraping_date = self.convert_to_yyyy_mm_dd(scraping_date)

        request = response.request
        url = request.url

        with fitz.open(stream=response.body, filetype="pdf") as pdf:
            pdf_title = pdf.metadata['title']
            pdf_author = pdf.metadata['author']
            pdf_date = self.convert_to_yyyy_mm_dd(pdf.metadata['creationDate'])

            # text, title, components = self.parse_pdf(pdf)
            extracted_text = "\n".join(page.get_text("text") for page in pdf)
            text=self.structure_content(extracted_text)
        title="Fallola"
        title = self.clean_title(title)

        pdf_title = response.url.split('/')[-1].replace('.pdf', '')

        loader = SrcaItemLoader(item=SrcaItem(), response=response)

        loader.add_value('title', title)
        loader.add_value('text', text)

        # Consolidate all metadata
        doc_type = [doc_types]
        url_type = response.headers.get('Content-Type', b'').decode('utf-8')
        file_path = "13.json"
        checksum = hashlib.md5(response.body).hexdigest()

        metadata = {
            'location': ['US'],
            'doc_types': doc_type,
            'published': pdf_date,
            'url': url,
            'url_type': url_type,
            'source_specific': {
                'publication_date': pdf_date,
                'information_types': None,
                'policy_areas': None,
                'company': None,
                'regulation_area': None,
                'breach_area': None,
                'closing_date': None,
                'status': None,
                'areas_covered': None,
                'author': pdf_author,
                'author_description': None
            },
            'file_urls': [url],
            # 'data_source': self.data_source,
            'files': [
                {
                    'url': url,
                    'path': file_path,
                    'checksum': checksum,  # Add checksum calculation if needed
                    'status': 'downloaded'
                }
            ],
            # 'components': components,
            # 'patterns': components,  # Assuming patterns match components
            'date_scraped': scraping_date,
            's3_urls': [],  # To be filled by pipeline
            's3_pdf_urls': [],  # To be filled by pipeline
            's3_key': None  # To be filled by pipeline
        }

        loader.add_value('meta_data', metadata)

        loader.add_value('html_body', None)

        item = loader.load_item()

        self.save_to_json(self.base_path+file_path, item)

        yield item


    # def parse(self, response):
    #     """
    #     Parses the response, extracts text, structures the content, and saves it.
    #     """
    #     print("\n[INFO] Loading PDF from response...")
    #     pdf_data = io.BytesIO(response.body)
    #     doc = fitz.open(stream=pdf_data, filetype="pdf")

    #     print("\n[INFO] Extracting text from PDF pages...")
    #     extracted_text = "\n".join(page.get_text("text") for page in doc)

    #     print("\n[INFO] Processing structured content...")
    #     structured_data = self.structure_content(extracted_text)

    #     print("\n[INFO] Saving structured content...")
    #     self.save_output(structured_data)

   
    
    def structure_content(self, text):
        """
        Extracts structured content from the PDF text, including articles, subarticles, sections, and paragraphs.
        """
        structured_data = {
            "text": []
        }

        chapter_pattern = re.compile(r"CHAPTER\s+(\d+)")
        article_pattern = re.compile(r"ARTICLE\s+(\d+)")
        subarticle_pattern = re.compile(r"SUBARTICLE\s+(\d+)\s*", re.IGNORECASE)
        section_pattern = re.compile(r"^13–(\d+)\.\s+(.*)")

        lines = text.split("\n")
        i = 0
        current_paragraph_content = ""

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Match Chapter
            match_chapter = chapter_pattern.match(line)
            if match_chapter:
                if current_paragraph_content:
                    structured_data["text"].append(f"[[PARAGRAPH]] {current_paragraph_content.strip()}")
                    current_paragraph_content = ""
                chapter_content = f"CHAPTER {match_chapter.group(1)}"
                if i + 1 < len(lines) and lines[i + 1].strip():
                    chapter_content += " " + lines[i + 1].strip()
                    i += 1
                structured_data["text"].append(f"[[CHAPTER]] {chapter_content}")
                i += 1
                continue

            # Match Articles
            match_article = article_pattern.match(line)
            if match_article:
                if current_paragraph_content:
                    structured_data["text"].append(f"[[PARAGRAPH]] {current_paragraph_content.strip()}")
                    current_paragraph_content = ""
                article_content = f"ARTICLE {match_article.group(1)}"
                if i + 1 < len(lines) and lines[i + 1].strip():
                    article_content += " " + lines[i + 1].strip()
                    i += 1
                structured_data["text"].append(f"[[ARTICLE]] {article_content}")
                i += 1
                continue

            # Match Subarticles
            match_subarticle = subarticle_pattern.match(line)
            if match_subarticle:
                if current_paragraph_content:
                    structured_data["text"].append(f"[[PARAGRAPH]] {current_paragraph_content.strip()}")
                    current_paragraph_content = ""
                subarticle_content = f"SUBARTICLE {match_subarticle.group(1)}"
                if i + 1 < len(lines) and lines[i + 1].strip():
                    subarticle_content += " " + lines[i + 1].strip()
                    i += 1
                structured_data["text"].append(f"[[SUBARTICLE]] {subarticle_content}")
                i += 1
                continue

            # Match Sections
            match_section = section_pattern.match(line)
            if match_section:
                if current_paragraph_content:
                    structured_data["text"].append(f"[[PARAGRAPH]] {current_paragraph_content.strip()}")
                    current_paragraph_content = ""
                section_content = f"SECTION {match_section.group(1)} {match_section.group(2)}"
                structured_data["text"].append(f"[[SECTION]] {section_content}")
                i += 1
                continue

            # Accumulate paragraph content
            current_paragraph_content += line + " "
            i += 1

        # Append any remaining paragraph content
        if current_paragraph_content:
            structured_data["text"].append(f"[[PARAGRAPH]] {current_paragraph_content.strip()}")

        return structured_data


    def save_output(self, data):
        """
        Saves structured data in one write operation.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"\n[SUCCESS] Saved structured data to {self.save_path}")

##########################################################################################

    def convert_to_yyyy_mm_dd(self,date_str):
        # List of possible date formats
        date_formats = [
            "%Y%m%d%H%M%S",      # PDF format without timezone
            "%Y%m%d%H%M%S%z",    # PDF format with timezone
            "%Y-%m-%d %H:%M:%S",   # Standard format with time
            "%Y-%m-%d",            # Standard format without time
            "%m/%d/%Y",            # US format MM/DD/YYYY
            "%d/%m/%Y",            # European format DD/MM/YYYY
            "%Y%m%d%H%M%S",        # Compact format
            "%Y%m%d"               # Compact date-only format
        ]
        
        # Remove the 'D:' prefix if present
        if date_str.startswith("D:"):
            date_str = date_str[2:]
        
        # Normalize timezone format if present (e.g., "-07'00''" to "-0700")
        if "'" in date_str:
            date_str = date_str.replace("'", "")

        # Try each format until one works
        for fmt in date_formats:
            try:
                # Try to parse with the current format
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # If none of the formats matched, raise an error
        raise ValueError(f"Date format for '{date_str}' is not recognized.")
    def clean_title(self,title: str) -> str:
        """
        Cleans the input title by removing quotes, reducing spaces,
        and normalizing multiple dashes into a single dash.

        Args:
            title (str): The input title to be cleaned.

        Returns:
            str: The cleaned and normalized title.
        """
        # Remove single and double quotes
        title = re.sub(r"[\"']", "", title)

        # Replace multiple spaces with a single space
        title = re.sub(r'\s+', ' ', title)

        # Normalize multiple dashes to a single dash
        title = re.sub(r'-{2,}', '-', title)

        # Strip leading/trailing spaces and dashes
        return title.strip(' -')

    def clean_reg_id(self,reg_id: str) -> str:
        """
        Cleans the input registration ID by replacing spaces and special characters
        with dashes and normalizing multiple dashes into a single dash.

        Args:
            reg_id (str): The input registration ID to be cleaned.

        Returns:
            str: The cleaned and normalized registration ID.
        """
        # Replace all whitespace with a dash
        reg_id = re.sub(r'\s+', '-', reg_id)

        # Replace special characters with a dash
        reg_id = re.sub(r'[^\w\-]', '-', reg_id)

        # Normalize multiple dashes to a single dash
        reg_id = re.sub(r'-{2,}', '-', reg_id)

        # Strip leading/trailing dashes
        return reg_id.strip('-')
    def save_to_json(self, file_path, data):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dict(data), f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save JSON file {file_path}: {str(e)}")