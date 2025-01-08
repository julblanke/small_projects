import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))

from search_engine.src.crawler import Crawler
from flask import Flask, render_template, request


template_folder = "../templates_search_engine"
app = Flask(__name__, template_folder=template_folder)


@app.route('/')
def home() -> str:
    """Renders Homepage from template in 'templates_search_engine'-directory.

    Returns:
        html_string (str): Html string of home page template.
    """
    return render_template("search_engine_home.html")


@app.route('/search', methods=['GET'])
def search() -> str:
    """Run search engine.

    Returns:
        html_content (str): Html string of content to display or error-string to display.
    """
    crawler = Crawler(url="https://vm009.rz.uos.de/crawl/index.html")
    crawler.crawl()

    query = request.args.get('q')
    if query:
        search_results = crawler.search_index(query_string=query)
        return render_template(
            "search_engine_results.html",
            results=search_results,
            query=query
        )
    else:
        return 'No search query provided.'


if __name__ == '__main__':
    app.run(debug=True)
