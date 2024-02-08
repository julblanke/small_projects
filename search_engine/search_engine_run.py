import os
from flask import Flask, render_template, request
from search_engine.crawler import Crawler


template_folder = os.path.join(os.getcwd(), "search_engine", "templates_search_engine")
app = Flask(__name__, template_folder=template_folder)


@app.route('/')
def home() -> str:
    """Renders Homepage from template in 'templates_search_engine'-directory.

    Returns:
        html_string (str): Html string of home page template
    """
    return render_template("search_engine_home.html")


@app.route('/search', methods=['GET'])
def search() -> str:
    """Run search engine.

    Returns:
        html_content (str): Html string of content to display or error-string to display
    """
    # crawls test server and creates index
    crawler = Crawler(url="https://vm009.rz.uos.de/crawl/index.html")
    crawler.crawl()

    # takes query, searches index and returns hits as html-string with links, title and content
    query = request.args.get('q')
    if query:
        search_results = crawler.search_index(query_string=query)
        if search_results:
            links_html = ''.join([f'<li><a href="{url}">{title}</a></li><p>{teaser}</p>'
                                  for url, content, title, teaser in search_results])
            html_content = f'<ul>{links_html}</ul>'
            return html_content
        else:
            return f'No items found with query: {query}'
    else:
        return 'No search query provided.'


if __name__ == '__main__':
    app.run(debug=True)
