from src.utils import get_llm, limited_web_search
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

# def generate_enriched_response(user_inputs, config_path="src/config.yaml"):
#     llm = get_llm(config_path)
#     final_output = ""
#     sources_used = []

#     # Check if all sections are empty
#     if all(not user_inputs.get(section, "").strip() for section in SECTION_LABELS):
#         return ("Please fill out the form to generate your NSF Facilities Template.", [])

#     for section in SECTION_LABELS:
#         user_text = user_inputs.get(section, "").strip()
#         if not user_text:
#             continue

#         query = f"{section}: {user_text}"

#         retrieved = search_similar_chunks(query, k=5, config_path=config_path)
#         retrieved_chunks = [
#             f"{doc.page_content}\n(Source: {doc.metadata.get('source', 'unknown')})"
#             for doc in retrieved
#         ]
#         retrieved_texts_with_sources = "\n\n".join(retrieved_chunks)
#         source_refs = [doc.metadata.get("source", "unknown") for doc in retrieved]

#         web_content, web_links = limited_web_search(query, config_path=config_path)

#         prompt = PROMPT_TEMPLATE.format(
#             section=section,
#             user_input=user_text,
#             retrieved_chunks=retrieved_texts_with_sources,
#             web_snippets=web_content
#         )

#         result = llm.invoke(prompt)
#         response_text = result.content.strip()
#         final_output += f"\n\n## {section}\n\n{response_text}\n"

#         cited_sources = [src for src in source_refs if f"(Source: {src})" in response_text]
#         sources_used.extend(cited_sources)

#     return final_output.strip(), list(set(sources_used + web_links))

def generate_enriched_response(user_inputs, config_path="src/config.yaml"):
    llm = get_llm(config_path)
    section_outputs = {}  # <-- dict instead of final_output string!
    sources_used = []

    # Check if all sections are empty
    if all(not user_inputs.get(section, "").strip() for section in SECTION_LABELS):
        return ({}, [])  # Return empty dict

    for section in SECTION_LABELS:
        user_text = user_inputs.get(section, "").strip()
        if not user_text:
            continue

        query = f"{section}: {user_text}"

        retrieved = search_similar_chunks(query, k=5, config_path=config_path)
        retrieved_chunks = [
            f"{doc.page_content}\n(Source: {doc.metadata.get('source', 'unknown')})"
            for doc in retrieved
        ]
        retrieved_texts_with_sources = "\n\n".join(retrieved_chunks)
        source_refs = [doc.metadata.get("source", "unknown") for doc in retrieved]

        web_content, web_links = limited_web_search(query, config_path=config_path)

        prompt = PROMPT_TEMPLATE.format(
            section=section,
            user_input=user_text,
            retrieved_chunks=retrieved_texts_with_sources,
            web_snippets=web_content
        )

        result = llm.invoke(prompt)
        response_text = result.content.strip()

        # Save each section individually!
        section_outputs[section] = response_text

        cited_sources = [src for src in source_refs if f"(Source: {src})" in response_text]
        sources_used.extend(cited_sources)
        # Only keep web links that are actually cited in the response text
        cited_web_links = [
            link for link in web_links if f"(Web Source: {link})" in response_text
        ]
        sources_used.extend(cited_web_links)

    return section_outputs, list(set(sources_used))
