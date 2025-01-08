import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from urllib.parse import urlparse, urljoin
from whoosh.fields import Schema, TEXT, ID, DATETIME


class Crawler:
    """Crawls given url for links, title, meta description, and content,
    then creates a Whoosh index. On query input, searches the index and returns hits.

    Attributes:
        url (str): String of the starting URL to crawl.
    """
    def __init__(self, url: str) -> None:
        """Constructor."""
        self.url = url
        self.parsed_based_url = urlparse(url)
        self.visited_urls = set()
        self.results = []

        # setup Whoosh
        self.schema = Schema(
            url=ID(unique=True, stored=True),
            content=TEXT(stored=True),
            title=TEXT(stored=True),
            teaser=TEXT(stored=True),
            description=TEXT(stored=True),
            crawled_at=DATETIME(stored=True)
        )
        index_path = "../search_engine/index"
        if not os.path.exists(index_path):
            os.makedirs(index_path)
        self.index = create_in(index_path, self.schema)
        self.writer = self.index.writer()

    def crawl(self) -> None:
        """Crawls the given URL and sub-URLs and creates a Whoosh index."""
        visited_urls = set()
        url_queue = [self.url]

        while url_queue:
            current_url = url_queue.pop(0)
            if current_url not in visited_urls:
                visited_urls.add(current_url)
                html = self._fetch_and_parse(current_url)

                if html:
                    soup = BeautifulSoup(html, 'html.parser')

                    # get title
                    title = soup.title.string if soup.title else current_url

                    # get teaser text
                    teaser_elem = soup.find('p')
                    teaser = teaser_elem.text if teaser_elem else "No teaser available"

                    # get meta description
                    meta_description = soup.find('meta', attrs={'name': 'description'})
                    description = meta_description['content'] if meta_description else "No description available"

                    # get links and extend URL queue
                    links = self._extract_links(html, current_url, self.parsed_based_url)
                    url_queue.extend(links)

                    # get all text from the page
                    page_text = soup.get_text(separator=" ")

                    # clean up lines like "Page 2 This is Page 2" or the title line
                    cleaned_text = self._clean_content(page_text, title)

                    self.writer.add_document(
                        url=current_url,
                        content=cleaned_text,
                        title=title,
                        teaser=teaser,
                        description=description,
                        crawled_at=datetime.now()
                    )
        self.writer.commit()

    def search_index(self, query_string: str) -> list:
        """Parses query and searches index for hits, return results as list.

        Args:
            query_string (str): The search query.

        Returns:
            results (list): A list of search result entries, containing "url, sentence_with_query, title, teaser and
                            description".
        """
        results = []
        with self.index.searcher() as searcher:
            query_parser = QueryParser("content", schema=self.index.schema)
            query = query_parser.parse(query_string)

            results_query = searcher.search(query, terms=True, limit=50)

            for hit in results_query:
                content = hit['content']
                # find the sentence containing the query term
                sentence_with_query = self._extract_sentence_with_query(content, query_string)

                results.append([
                    hit['url'],
                    sentence_with_query,
                    hit['title'],
                    hit['teaser'],
                    hit['description']
                ])
        return results

    @staticmethod
    def _clean_content(page_text: str, title: str) -> str:
        """Removes lines that match or contain the page title or start with phrases like 'This is Page' to filter out
           undesired concatenation.

        Args:
            page_text (str): Original text content from the page.
            title (str): The page title found in <title>.

        Returns:
            cleaned_text (str): The cleaned text without the undesired lines.
        """
        skip_phrases = [title.lower(), "this is page "]
        cleaned_lines = []

        for line in page_text.split('\n'):
            lower_line = line.strip().lower()

            # skips the line if it matches any undesired phrase or starts with them
            if any(lower_line.startswith(sp) or lower_line == sp for sp in skip_phrases):
                continue
            cleaned_lines.append(line.strip())

        cleaned_text = ". ".join(cleaned_lines)
        return cleaned_text

    @staticmethod
    def _extract_sentence_with_query(content: str, query: str) -> str:
        """Extracts the first sentence containing the query from the content.

        Args:
            content (str): The full content text.
            query (str): The search query.

        Returns:
            (str): The sentence containing the query  (or a fallback if not found).
        """
        sentences = content.split('.')
        for sentence in sentences:
            if query.lower() in sentence.lower():
                return sentence.strip() + '.'
        return "No matching sentence found."

    @staticmethod
    def _fetch_and_parse(current_url: str) -> str:
        """Establishes connection to url, fetches and parses website content.

        Returns:
            response (str): Current url's content.
        """
        try:
            with requests.Session() as session:
                requests.packages.urllib3.util.connection.HAS_IPV6 = False
                response = session.get(current_url)
            if response.status_code == 200:
                return response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {current_url}: {e}")
        return None

    @staticmethod
    def _extract_links(html: str, base_url: str, parsed_base_url) -> set:
        """Searches given html string of current url for links.

        Args:
            html (str): Html content str of current url.
            base_url (str): String of initial url (starting url of crawling).
            parsed_base_url (str): Parsed url of initial url (starting url of crawling).

        Returns:
            links (set(str)): Set of links found in current url.
        """
        links = set()
        soup = BeautifulSoup(html, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)
            if urlparse(absolute_url).netloc == parsed_base_url.netloc:
                links.add(absolute_url)
        return links
