import yaml
from portkey_ai import createHeaders
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

def read_yaml_as_dict(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_llm(config_path="src/config.yaml", model_name="gpt-4o"):
    config = read_yaml_as_dict(config_path)
    headers = createHeaders(
        api_key=config["portkey"]["chat"]["api_key"],
        virtual_key=config["portkey"]["chat"]["openai_virtual_key"]
    )
    return ChatOpenAI(
        api_key="unused",
        base_url=config["portkey"]["base_url"],
        default_headers=headers,
        model=model_name
    )

def get_embedding_model(config_path="src/config.yaml"):
    config = read_yaml_as_dict(config_path)
    headers = createHeaders(
        api_key=config["portkey"]["embeddings"]["api_key"],
        virtual_key=config["portkey"]["embeddings"]["virtual_key"]
    )
    return OpenAIEmbeddings(
        api_key="unused",
        base_url=config["portkey"]["base_url"],
        default_headers=headers
    )

from langchain.tools.tavily_search import TavilySearchResults
from langchain_community.tools.tavily_search import TavilySearchResults
from tavily import TavilyClient  





from tavily import TavilyClient
from src.utils import read_yaml_as_dict

def limited_web_search(query: str, config_path="src/config.yaml") -> tuple[str, list[str]]:
    config = read_yaml_as_dict(config_path)
    api_key = config.get("tavily", {}).get("TAVILY_API_KEY")

    if not api_key:
        return "", []

    client = TavilyClient(api_key=api_key)
    snippets = []
    urls = []

    
    from urllib.parse import urlparse

    allowed_domains = ["nyu.edu", "nsf.gov"]
    blocklist = [
        "https://med.nyu.edu/research/scientific-cores-shared-resources/high-performance-computing-core"
    ]

    try:
        for domain in allowed_domains:
            response = client.search(
                query=f"site:{domain} {query}",
                search_depth="advanced",
                max_results=3
            )
            for r in response.get("results", []):
                url = r.get("url", "").strip()
                content = r.get("content", "").strip()

                parsed_domain = urlparse(url).netloc  
                
                if (
                    any(allowed in parsed_domain for allowed in allowed_domains)
                    and not any(url.startswith(bad) for bad in blocklist)
                ):
                    snippets.append(f"{content}\n(Web Source: {url})")
                    urls.append(url)


    except Exception as e:
        snippets.append(f"Web search failed: {e}")

    return "\n\n".join(snippets), urls

def limited_web_search_specific_sites(query: str, allowed_sites: list[str], config_path="src/config.yaml") -> tuple[str, list[str]]:
    """
    Perform a Tavily web search but only within the explicitly allowed sites.
    Only include snippets and URLs from the exact allowed domains.
    """
    config = read_yaml_as_dict(config_path)
    api_key = config.get("tavily", {}).get("TAVILY_API_KEY")

    if not api_key:
        return "", []

    client = TavilyClient(api_key=api_key)
    snippets = []
    urls = []

    try:
        for site in allowed_sites:
            response = client.search(
                query=f"site:{site} {query}",
                search_depth="advanced",
                max_results=3
            )
            for r in response.get("results", []):
                url = r.get("url", "")
                content = r.get("content", "").strip()

                if any(url.startswith(s) for s in allowed_sites):
                    # Optional: You can filter the snippet content if needed
                    snippets.append(f"{content}\n(Web Source: {url})")
                    urls.append(url)

    except Exception as e:
        snippets.append(f"Web search failed: {e}")

    return "\n\n".join(snippets), urls
