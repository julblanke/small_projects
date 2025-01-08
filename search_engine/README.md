# Search Engine University Project

This project is a simple web-based search engine that crawls a given URL, indexes the extracted 
content using Whoosh, and provides a search interface via Flask. It also includes 
a user interface with optional Dark Mode.

## Getting Started

Install the dependencies via:
```bash
pip install -r requirements.txt
```

## How to Run

1. Clone or download this repository.
2. Navigate to the src directory.
3. Activate your venv.
4. Run the Flask app via:
```bash
python search_engine_run.py 
```
5. Open your browser and visit **`http://127.0.0.1:5000/`**.

## Usage

1. On the home page, type your **search query** into the input box and click **Search**.
2. Results appear with:
- **Title** linked to the original page.
- **URL** of the page.
- **Text Snippet** showing a highlighted or extracted portion of text containing the query term.
- **Meta Description** if available.

3. An optional **Dark Mode** toggle is provided on each page.

## Customization

**Crawling Start URL**: In `search_engine_run.py`, look for:
```python
crawler = Crawler(url="https://vm009.rz.uos.de/crawl/index.html")
```
