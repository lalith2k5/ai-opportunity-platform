import requests
import xml.etree.ElementTree as ET
from app.logger import logger
from app.services.retry_helper import api_retry


class ArxivService:
    BASE_URL = "http://export.arxiv.org/api/query"
    HARD_CAP = 200

    @api_retry(max_attempts=3)
    def _get(self, params):
        return requests.get(self.BASE_URL, params=params, timeout=30)

    def search_papers(self, query: str, max_results: int = 10):
        max_results = min(max_results, self.HARD_CAP)
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            response = self._get(params)
            if response.status_code != 200:
                logger.warning(f"arXiv status {response.status_code}")
                return []
            papers = self._parse_response(response.text)
            logger.info(f"arXiv: fetched {len(papers)} papers for '{query}'")
            return papers
        except Exception as e:
            logger.error(f"arXiv error: {e}")
            return []

    def _parse_response(self, xml_text):
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []
        papers = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            id_el = entry.find("atom:id", ns)
            papers.append({
                "id": id_el.text if id_el is not None else "",
                "title": title_el.text.strip() if title_el is not None else "",
                "summary": summary_el.text.strip() if summary_el is not None else "",
                "authors": [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None],
                "url": id_el.text if id_el is not None else "",
            })
        return papers
