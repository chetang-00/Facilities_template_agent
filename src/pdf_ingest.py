import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from src.utils import get_embedding_model, read_yaml_as_dict

def ingest_pdfs(data_folder="data", config_path="src/config.yaml"):
    config = read_yaml_as_dict(config_path)
    persist_dir = config["chroma"]["persist_directory"]
    embedding = get_embedding_model(config_path)
    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for file in os.listdir(data_folder):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(data_folder, file))
            docs = loader.load()
            chunks = splitter.split_documents(docs)
            for c in chunks:
                c.metadata["source"] = file
            all_chunks.extend(chunks)

    vectordb = Chroma.from_documents(all_chunks, embedding=embedding, persist_directory=persist_dir)
    vectordb.persist()
