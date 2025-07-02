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
from tavily import TavilyClient  # official SDK



# def limited_web_search(query: str, config_path="src/config.yaml") -> str:
#     config = read_yaml_as_dict(config_path)
#     api_key = config["tavily"]["TAVILY_API_KEY"]
#     if not api_key:
#         return ""

#     search_tool = TavilySearchResults(k=3, tavily_api_key=api_key)

#     results = []
#     try:
#         nyu_result = search_tool.run(f"site:nyu.edu {query}")
#         if nyu_result:
#             results.append(f"From nyu.edu:\n{nyu_result}")

#         nsf_result = search_tool.run(f"site:nsf.gov {query}")
#         if nsf_result:
#             results.append(f"From nsf.gov:\n{nsf_result}")
#     except Exception as e:
#         results.append(f"Web search failed: {e}")

#     return "\n\n".join(results)


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

    try:
        for domain in ["nyu.edu", "nsf.gov"]:
            response = client.search(
                query=f"site:{domain} {query}",
                search_depth="advanced",
                max_results=3
            )
            for r in response.get("results", []):
                if r.get("content") and r.get("url"):
                    snippets.append(f"{r['content'].strip()}\n(Web Source: {r['url']})")
                    urls.append(r['url'])

    except Exception as e:
        snippets.append(f"Web search failed: {e}")

    return "\n\n".join(snippets), urls


