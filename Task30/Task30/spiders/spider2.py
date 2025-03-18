import scrapy
from datetime import datetime
from ..spider_templates.basespiderv2 import BaseSpiderV2
import fitz
import re
from ..items import SrcaItem
from ..itemsLoaders import SrcaItemLoader
import os, json, hashlib

# this spider inherits the basespiderv2
class Spider2(BaseSpiderV2):
    name = "scag"
    data_source = "SCAG"
    base_path = f"output_data/{name}/"
    def parse(self, response, doc_types=None):
        
        scraping_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scraping_date = self.convert_to_yyyy_mm_dd(scraping_date)

        request = response.request
        url = request.url

        with fitz.open(stream=response.body, filetype="pdf") as pdf:
            pdf_title = pdf.metadata['title']
            pdf_author = pdf.metadata['author']
            pdf_date = self.convert_to_yyyy_mm_dd(pdf.metadata['creationDate'])

            text, title, components = self.parse_pdf(pdf)

        title = self.clean_title(title)

        pdf_title = response.url.split('/')[-1].replace('.pdf', '')

        loader = SrcaItemLoader(item=SrcaItem(), response=response)

        loader.add_value('title', title)
        loader.add_value('text', text)

        # Consolidate all metadata
        doc_type = [doc_types]
        url_type = response.headers.get('Content-Type', b'').decode('utf-8')
        file_path = f"{self.data_source}/{doc_type[0]}/json/{pdf_title}.json"
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
                'regulation_area': 'South Carolina',
                'breach_area': None,
                'closing_date': None,
                'status': None,
                'areas_covered': None,
                'author': pdf_author,
                'author_description': None
            },
            'file_urls': [url],
            'data_source': self.data_source,
            'files': [
                {
                    'url': url,
                    'path': file_path,
                    'checksum': checksum,  
                    'status': 'downloaded'
                }
            ],
            'components': components,
            'patterns': components,  
            'date_scraped': scraping_date,
            's3_urls': [],  
            's3_pdf_urls': [], 
            's3_key': None 
        }

        loader.add_value('meta_data', metadata)

        loader.add_value('html_body', None)

        item = loader.load_item()

        self.save_to_json(self.base_path+file_path, item)

        yield item


    def clean_text(self, text):
        """Clean text by removing extra spaces and normalizing whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,;:!?)])', r'\1', text)
        # Remove spaces after opening parenthesis
        text = re.sub(r'(\()\s+', r'\1', text)
        # Trim whitespace
        text = text.strip()
        return text


    def concatenate_until_end(self, strings):
        # after processing each line separately, we need to identify the lines that are related to the same tag
        concatenated_strings = []
        i = 0

        while i < len(strings):
            current_string = strings[i]
            flag=False
            if (current_string.startswith("[[CHAPTER]]") or 
                current_string.startswith("[[ARTICLE]]") or 
                current_string.startswith("[[SUBARTICLE]]") or
                current_string.startswith("[[HISTORY]]") or
                current_string.startswith("[[POINT]]")):
                flag=True
                while flag:
                    if(i+1<len(strings)):
                        if strings[i+1].startswith("[[PARAGRAPH]]"):
                            current_string += ' ' + strings[i+1].split("[[PARAGRAPH]] ")[1]
                            i=i+1
                        elif ((not current_string.endswith('.')) and strings[i+1].startswith("[[POINT]]")):
                            current_string += ' ' + strings[i+1].split("[[POINT]] ")[1]
                            i=i+1
                        else:
                            flag=False
                    else:
                        flag=False
            elif current_string.startswith("[[SECTION]]"):
                if not current_string.endswith("."):
                    flag=True
                    while flag:
                        if strings[i+1].startswith("[[PARAGRAPH]]") and strings[i+1].endswith("."):
                            current_string += ' ' + strings[i+1].split("[[PARAGRAPH]] ")[1]
                            i=i+1
                            flag=False
                            break
            elif current_string.startswith("[[PARAGRAPH]]"):
                flag=True
                while flag:
                    if(i+1<len(strings)):
                        if strings[i+1].startswith("[[PARAGRAPH]]"):
                            current_string += ' ' + strings[i+1].split("[[PARAGRAPH]] ")[1]
                            i=i+1
                        else:
                            flag=False
                    else:
                        flag=False

            current_string = self.clean_text(current_string)
            concatenated_strings.append(current_string)
            i += 1  

        return concatenated_strings

    def parse_pdf(self, doc):
        article_tag = "[[ARTICLE]]"
        subarticle_tag = "[[SUBARTICLE]]"
        chapter_tag = "[[CHAPTER]]"
        section_tag = "[[SECTION]]"
        paragraph_tag = "[[PARAGRAPH]]"
        history_tag="[[HISTORY]]"
        code_tag="[[CODE]]"
        point_tag="[[POINT]]"
        
        

        results = []
        used_tags = set()  # Set to store unique tags that were used
        title = ''

        chapter_pattern = re.compile(r"CHAPTER\s+(\d+)")
        article_pattern = re.compile(r"ARTICLE\s+(\d+)")
        subarticle_pattern = re.compile(r"SUBARTICLE\s+(\d+)\s*")
        section_pattern = re.compile(r"^\d+–(\d+)\.\s+(.*)")
        history_pattern = re.compile(r"^HISTORY:")
        code_pattern = re.compile(r"^\(Statutory Authority: .* Code .*?\)$")
        point_pattern = re.compile(r"^[A-Z]\.[\s\S]+$")
        # point_pattern = re.compile(r"^(?:\((?:\d+|[A-Za-z]|[IVXLCDMivxlcdm]+).+\)|(?:\d+|[A-Za-z]|[IVXLCDMivxlcdm]+)\..+)$")


        # Process each page in the PDF
        for page in doc:
            for text in page.get_text("dict")["blocks"]:
                lines = text["lines"]
                
                for i, line in enumerate(lines):
                    # Extract full line of text and then check if it matches any of the defined patterns
                    full_line_text = "".join(span["text"] for span in line["spans"]).replace("  ", " ").strip()          
                
                    if  chapter_pattern.match(full_line_text):
                        results.append(f"{chapter_tag} {full_line_text}")
                        used_tags.add(chapter_tag)
                    elif article_pattern.match(full_line_text):
                        results.append(f"{article_tag} {full_line_text}")
                        used_tags.add(article_tag)
                    elif subarticle_pattern.match(full_line_text):
                        results.append(f"{subarticle_tag} {full_line_text}")
                        used_tags.add(subarticle_tag)
                    elif section_pattern.match(full_line_text):
                        results.append(f"{section_tag} {full_line_text}")
                        used_tags.add(section_tag)
                    elif history_pattern.match(full_line_text):
                        results.append(f"{history_tag} {full_line_text}")
                        used_tags.add(history_tag)
                    elif code_pattern.match(full_line_text):
                        results.append(f"{code_tag} {full_line_text}")
                        used_tags.add(code_tag)
                    elif point_pattern.match(full_line_text):
                        results.append(f"{point_tag} {full_line_text}")
                        used_tags.add(point_tag)
                    else:
                        results.append(f"{paragraph_tag} {full_line_text}")
                        used_tags.add(paragraph_tag)

        clean_results = self.concatenate_until_end(results)
        # get the title from the first line after the tag
        title=clean_results[0].split("]] ")[1]
        return clean_results, title, list(used_tags)  


    def save_to_json(self, file_path, data):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dict(data), f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save JSON file {file_path}: {str(e)}")