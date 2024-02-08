import os
import re
import requests
import numpy as np
from bs4 import BeautifulSoup
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from urllib.parse import urlparse, urljoin
from whoosh.fields import Schema, TEXT, ID


class Crawler:
    """Crawls given url for links, title and content and creates an index.
       On query input, searches given index and returns hits.
    """
    def __init__(self, url):
        """Constructor.

        Args:
            url (str): String of starting url to crawl
        """
        self.url = url
        self.parsed_based_url = urlparse(url)
        self.visited_urls = set()
        self.results = list()

        # setup whoosh
        self.schema = Schema(
            url=ID(unique=True, stored=True),
            content=TEXT(stored=True),
            title=TEXT(stored=True),
            teaser=TEXT(stored=True)
        )
        index_path = os.path.join(os.getcwd(), "search_engine", "index")
        self.index = create_in(index_path, self.schema)
        self.writer = self.index.writer()

    def crawl(self):
        """Crawls given url and sub-urls and creates index."""
        # setup crawling storage parameters
        visited_urls = set()
        url_queue = [self.url]

        # crawl through urls in url_queue
        while url_queue:
            current_url = url_queue.pop(0)

            if current_url not in visited_urls:
                visited_urls.add(current_url)
                html = Crawler._fetch_and_parse(current_url=current_url)

                # define title pattern to search for in html string of current url
                pattern_title = re.compile(r'<title>(.*?)</title>')
                matches_title = pattern_title.search(str(html))
                if matches_title:
                    title = matches_title.group(1)
                else:
                    title = current_url

                # define teaser text pattern to search for in html string of current url
                pattern_teaser = re.compile(r'<p>(.*?)</p>', re.DOTALL)
                matches_teaser = pattern_teaser.search(str(html))

                pattern_teaser_wo_slash = re.compile(r'<p>(.*?)<p>', re.DOTALL)
                matches_teaser_wo_slash = pattern_teaser_wo_slash.search(str(html))

                pattern_teaser_pre = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
                matches_teaser_pre = pattern_teaser_pre.search(str(html))

                # handles differences in html display of teaser text
                if matches_teaser:
                    teaser = matches_teaser.group(1)
                else:
                    teaser = current_url
                if matches_teaser_wo_slash:
                    teaser = matches_teaser_wo_slash.group(1)
                if matches_teaser_pre:
                    teaser = matches_teaser_pre.group(1)

                # extends url queue if new links were found in current website
                if html:
                    links = Crawler._extract_links(html, current_url, parsed_base_url=self.parsed_based_url)
                    url_queue.extend(links)

                # add to whoosh index
                self.writer.add_document(url=current_url, content=html, title=title, teaser=teaser)
        self.writer.commit()

    def search_index(self, query_string) -> np.array:
        """Parses query and searches index for hits, return results as array."""
        results = []
        with self.index.searcher() as searcher:
            query_parser = QueryParser("content", schema=self.index.schema)
            query = query_parser.parse(query_string)
            results_query = searcher.search(query)
            for hit in results_query:
                results.append([hit['url'], hit['content'], hit['title'], hit['teaser']])
        return results

    @staticmethod
    def _fetch_and_parse(current_url) -> str:
        """Establishes connection to url, fetches and parses website content.

        Returns:
            response (str): Current url's content
        """
        try:
            with requests.Session() as session:
                requests.packages.urllib3.util.connection.HAS_IPV6 = False
                response = session.get(current_url)
            if response.status_code == 200:
                return response.text
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch {current_url}: {e}")

    @staticmethod
    def _extract_links(html, base_url, parsed_base_url) -> set:
        """Searches given html string of current url for links.

        Args:
            html (str): Html content str of current url
            base_url (str): String of initial url (starting url of crawling)
            parsed_base_url (str): Parsed url of initial url (starting url of crawling)

        Returns:
            links (set(str)): Set of links found in current url
        """
        links = set()
        soup = BeautifulSoup(html, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)

            # check if the link is on the same server
            if parsed_url.netloc == parsed_base_url.netloc:
                links.add(absolute_url)
        return links
