from langchain.vectorstores import Chroma
from src.utils import get_embedding_model, read_yaml_as_dict

def search_similar_chunks(query, k=5, config_path="src/config.yaml"):
    config = read_yaml_as_dict(config_path)
    persist_dir = config["chroma"]["persist_directory"]
    embedding = get_embedding_model(config_path)

    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    return retriever.get_relevant_documents(query)
