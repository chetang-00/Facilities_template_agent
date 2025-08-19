import os
import time
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
    
    already_processed = set()
    try:
        existing_db = Chroma(persist_directory=persist_dir, embedding_function=embedding)
        # get all documents from existing database
        existing_docs = existing_db.get()
        if existing_docs and existing_docs['metadatas']:
            for metadata in existing_docs['metadatas']:
                if metadata and 'source' in metadata:
                    already_processed.add(metadata['source'])
        print(f"Found {len(already_processed)} already processed files")
    except Exception as e:
        print(f"No existing database found or error loading it: {e}")

    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, data_folder)
                
                # Skip if file is already processed
                if file in already_processed:
                    print(f"Skipping already processed file: {relative_path}")
                    continue
                
                max_retries = 2
                for attempt in range(max_retries + 1):
                    try:
                        print(f"Processing: {relative_path} (attempt {attempt + 1})")
                        
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                        chunks = splitter.split_documents(docs)
                        for c in chunks:
                            c.metadata["source"] = file
                            c.metadata["folder"] = os.path.dirname(relative_path) if os.path.dirname(relative_path) else "root"
                        
                        print(f"  PDF loaded and split into {len(chunks)} chunks, now creating embeddings...")
                        
                        
                        if all_chunks: 
                            existing_db = Chroma(persist_directory=persist_dir, embedding_function=embedding)
                            existing_db.add_documents(chunks)
                            existing_db.persist()
                        else:  # First file, create new database
                            vectordb = Chroma.from_documents(chunks, embedding=embedding, persist_directory=persist_dir)
                            vectordb.persist()
                        
                        all_chunks.extend(chunks)
                        print(f"Successfully processed {relative_path} ({len(chunks)} chunks)")
                        break 
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"Error processing {relative_path} (attempt {attempt + 1}): {error_msg}")
                        
                        if "429" in error_msg or "rate limit" in error_msg.lower():
                            print(f"  Rate limit detected! This is attempt {attempt + 1} of {max_retries + 1}")
                            if attempt < max_retries:
                                print(f"  Waiting 60 seconds before retry...")
                                time.sleep(60)
                            else:
                                print(f"  Failed after {max_retries + 1} attempts due to rate limiting")
                        else:
                            print(f"  Non-rate-limit error. This is attempt {attempt + 1} of {max_retries + 1}")
                            if attempt < max_retries:
                                print(f"  Waiting 60 seconds before retry...")
                                time.sleep(60)
                            else:
                                print(f"  Failed after {max_retries + 1} attempts")
                        
                        if attempt == max_retries:
                            print(f"Failed to process {relative_path} after {max_retries + 1} attempts")
                
                print("Waiting 30 seconds before next file...")
                time.sleep(30)

    if all_chunks:
        print(f"Processing complete. Total chunks processed: {len(all_chunks)}")
        print(f"Vector database updated and persisted to {persist_dir}")
    else:
        print("No PDF chunks found to process.")
