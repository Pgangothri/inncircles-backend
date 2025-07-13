import os
import sys
import requests

# Add project root for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
from src.utils.config_loader import load_config
from src.utils.logging_config import logger
from src.utils.xml_formatter import xml_wrap  # ✅ Use standard formatter

# Load environment variables
load_dotenv()

# Load tool config
tool_cfg = load_config("tools_config.yaml")
config = tool_cfg["tools"]["web_search"]


class WebSearchTool:
    def __init__(self):
        self.tag = "web_search"
        self.api_key = os.getenv("SERPAPI_KEY") or config.get("api_key")
        self.max_results = config.get("max_results", 5)
        self.paywall_keywords = [
            "subscribe", "login to continue", "access denied",
            "restricted content", "404", "this page is not working"
        ]
        logger.info("[WebSearch] Initialized with max_results=%d", self.max_results)

    def link_valid(self, link):
        if not link.startswith("http"):
            logger.warning("[WebSearch] Invalid link: %s", link)
            return "Status: Invalid URL"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(link, headers=headers, timeout=5)
            status = response.status_code
            if status == 200:
                content = response.text[:1000].lower()
                if any(k in content for k in self.paywall_keywords):
                    return "Status: Possible Paywall"
                return "Status: OK"
            return f"Status: {status} {response.reason}"
        except requests.RequestException as e:
            return f"Error: {str(e)}"

    def check_all_links(self, links):
        return [self.link_valid(link) for link in links]

    def execute(self, query: str, task_id="web_search_task_001") -> str:
        if not self.api_key:
            return xml_wrap(
                task_id,
                status="failed",
                current_step=self.tag,
                tools_used=["web_search"],
                reasoning={"thought": "Missing API key", "next_action": "abort"},
                result={"success": False, "data": [], "errors": ["Missing SERPAPI_KEY"]}
            )

        query = query.strip()
        if not query:
            return xml_wrap(
                task_id,
                status="failed",
                current_step=self.tag,
                tools_used=["web_search"],
                reasoning={"thought": "Empty query", "next_action": "abort"},
                result={"success": False, "data": [], "errors": ["Query was empty"]}
            )

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": self.max_results,
                "output": "json"
            }
            resp = requests.get("https://serpapi.com/search", params=params)
            resp.raise_for_status()
            data = resp.json()

            if "organic_results" not in data or not data["organic_results"]:
                return xml_wrap(
                    task_id,
                    status="completed",
                    current_step=self.tag,
                    tools_used=["web_search"],
                    reasoning={"thought": "No search results found", "next_action": "stop"},
                    result={"success": True, "data": [], "errors": []}
                )

            final_results = []
            organic_results = data["organic_results"][:self.max_results]
            links = [r.get("link", "") for r in organic_results]
            statuses = self.check_all_links(links)

            for r, status in zip(organic_results, statuses):
                if "OK" not in status:
                    continue
                final_results.append({
                    "title": r.get("title", "No title"),
                    "snippet": r.get("snippet", "No snippet"),
                    "link": r.get("link", "No link")
                })

            return xml_wrap(
                task_id,
                status="completed",
                current_step=self.tag,
                tools_used=["web_search"],
                reasoning={"thought": f"Processed search for '{query}'", "next_action": "use results"},
                result={"success": True, "data": final_results, "errors": []}
            )

        except requests.RequestException as e:
            return xml_wrap(
                task_id,
                status="failed",
                current_step=self.tag,
                tools_used=["web_search"],
                reasoning={"thought": "Network error during request", "next_action": "abort"},
                result={"success": False, "data": [], "errors": [str(e)]}
            )
        except Exception as e:
            return xml_wrap(
                task_id,
                status="failed",
                current_step=self.tag,
                tools_used=["web_search"],
                reasoning={"thought": "Unexpected failure in search tool", "next_action": "abort"},
                result={"success": False, "data": [], "errors": [str(e)]}
            )

    def execution_failure_check(self, output: str) -> bool:
        return "<status>failed</status>" in output or "<success>false</success>" in output

    def interpreter_feedback(self, output: str) -> str:
        if self.execution_failure_check(output):
            return f"[WebSearchTool] Failure:\n{output}"
        return f"[WebSearchTool] Success:\n{output}"

