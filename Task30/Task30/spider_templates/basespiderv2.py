import pkgutil

import scrapy
import re

import requests
import json

import abc

from datetime import datetime

class BaseSpiderV2(scrapy.Spider, abc.ABC):
    name = "base_spider_v2"
    start_urls = []  # Placeholders
    doc_types = []
    data_source = "Placeholder"
    requires_zip = False  # See start requests function

    def __init__(self):
        self.cached_urls = None

    def start_requests(self):
        """
        If there is a list of doc_types matching lengths, it will return
        the corresponding doc type for each url as a kwarg for parse
        requires_zip can be changed to true if this functionality is needed.
        """

        start_info = self.get_start_info()
        if start_info != []:
            for url_info in start_info:
                scrape_url = requests.utils.unquote(url_info["url"])
                doc_type = url_info["doc_type"]
                if url_info["active"]:
                    yield scrapy.Request(url=scrape_url, callback=self.parse, cb_kwargs={"doc_types": doc_type})
                else:
                    yield scrapy.Request(url=scrape_url, callback=self.parse)

    @abc.abstractmethod
    def parse(self, response, **kwargs):
        """
        Overwrite this in your spider
        """
        pass

    @staticmethod
    def clean_title(title: str) -> str:
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

    @staticmethod
    def clean_reg_id(reg_id: str) -> str:
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

    def get_start_info(self):
        # If some mutation on the url is needed, make your own
        # Or you can edit this function to allow you to pass an optional function?
        start_url_json = pkgutil.get_data(
            "Task30", f"spider_templates/spider_starturls.json"
        )
        print("start_url_json",start_url_json)

        spider_start_dict = json.loads(start_url_json)
        self.cached_urls = spider_start_dict
        return self.cached_urls.get(self.name, [])

    @property
    def start_urls(self):
        return [d.get("url") for d in self.get_start_info()]
    
    @staticmethod
    def convert_to_yyyy_mm_dd(date_str):
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

