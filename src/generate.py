from src.utils import get_llm, limited_web_search, limited_web_search_specific_sites
from src.retriever import search_similar_chunks
from prompt.prompt_template import PROMPT_TEMPLATE

SECTION_LABELS = [
    "1. Project Title",
    "2. Research Space and Facilities",
    "3. Core Instrumentation",
    "4. Computing and Data Resources",
    "5a. Internal Facilities (NYU)",
    "5b. External Facilities (Other Institutions)",
    "6. Special Infrastructure"
]


def generate_enriched_response(user_inputs, selected_types=None, config_path="src/config.yaml"):
    llm = get_llm(config_path)
    section_outputs = {} 
    sources_used = []

    if all(not user_inputs.get(section, "").strip() for section in SECTION_LABELS):
        return ({}, [])

    for section in SECTION_LABELS:
        user_text = user_inputs.get(section, "").strip()
        if not user_text:
            continue

        query = f"{section}: {user_text}"

        retrieved = search_similar_chunks(query, k=5, selected_types=selected_types, config_path=config_path)
        retrieved_chunks = [
            f"{doc.page_content}\n(Source: {doc.metadata.get('source', 'unknown')})"
            for doc in retrieved
        ]
        retrieved_texts_with_sources = "\n\n".join(retrieved_chunks)
        source_refs = [doc.metadata.get("source", "unknown") for doc in retrieved]

        if section == "5a. Internal Facilities (NYU)":
            web_content, web_links = limited_web_search_specific_sites(
                query,
                allowed_sites=[
                    "https://sites.google.com/nyu.edu/nyu-hpc/",
                    "https://www.nyu.edu/life/information-technology/research-computing-services/high-performance-computing.html",
                    "https://www.nyu.edu/life/information-technology/research-computing-services/high-performance-computing/high-performance-computing-nyu-it.html"
                ],
                config_path=config_path
            )
        else:
            web_content, web_links = limited_web_search(query, config_path=config_path)

        # web_content, web_links = limited_web_search(query, config_path=config_path)

        prompt = PROMPT_TEMPLATE.format(
            section=section,
            user_input=user_text,
            retrieved_chunks=retrieved_texts_with_sources,
            web_snippets=web_content
        )

        result = llm.invoke(prompt)
        response_text = result.content.strip()

        section_outputs[section] = response_text

        cited_sources = [src for src in source_refs if f"(Source: {src})" in response_text]
        sources_used.extend(cited_sources)

        cited_web_links = [
            link for link in web_links if f"(Web Source: {link})" in response_text
        ]
        sources_used.extend(cited_web_links)

    return section_outputs, list(set(sources_used))
