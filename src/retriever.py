from langchain.vectorstores import Chroma
from src.utils import get_embedding_model, read_yaml_as_dict

def search_similar_chunks(query, k=5, selected_types=None, config_path="src/config.yaml"):
    config = read_yaml_as_dict(config_path)
    persist_dir = config["chroma"]["persist_directory"]
    embedding = get_embedding_model(config_path)

    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedding)
    

    if selected_types:

        retriever = vectordb.as_retriever(search_kwargs={"k": k * 3})
        all_docs = retriever.get_relevant_documents(query)
        
        # filter documents based on file types
        filtered_docs = []
        for doc in all_docs:
            if doc.metadata and 'folder' in doc.metadata:
                folder = doc.metadata['folder']

                if any(selected_type in folder for selected_type in selected_types):
                    filtered_docs.append(doc)

                    if len(filtered_docs) >= k:
                        break
        
        return filtered_docs
    else:
        retriever = vectordb.as_retriever(search_kwargs={"k": k})
        return retriever.get_relevant_documents(query)
