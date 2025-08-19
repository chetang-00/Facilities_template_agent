import json
import numpy as np
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from langchain.vectorstores import Chroma
from src.utils import get_embedding_model, read_yaml_as_dict
from src.retriever import search_similar_chunks

def calculate_semantic_overlap(chunks, embedding_model):
    """Calculate semantic overlap using embeddings and cosine similarity"""
    if len(chunks) < 2:
        return 0.0
    
    try:
        # Get embeddings for all chunks
        print(" Calculating embeddings...")
        embeddings = []
        for i, chunk in enumerate(chunks):
            embedding = embedding_model.embed_query(chunk.page_content)
            embeddings.append(embedding)
            print(f"    Chunk {i+1}: {len(embedding)} dimensions")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings)
        
        # Calculate pairwise cosine similarities
        print(" Computing cosine similarities...")
        similarity_matrix = cosine_similarity(embeddings_array)
        
        # Calculate average similarity (excluding self-similarity)
        # Sum all similarities, subtract diagonal (self-similarity), divide by number of comparisons
        total_similarity = similarity_matrix.sum()
        self_similarity = np.trace(similarity_matrix)  # Sum of diagonal
        num_comparisons = len(chunks) * (len(chunks) - 1)  # Exclude self-comparisons
        
        if num_comparisons > 0:
            avg_similarity = (total_similarity - self_similarity) / num_comparisons
            return round(avg_similarity * 100, 2)  # Convert to percentage
        else:
            return 0.0
            
    except Exception as e:
        print(f" Error calculating semantic overlap: {e}")
        return 0.0

def calculate_source_diversity(chunks):
    """Calculate source diversity (how many different sources)"""
    sources = [doc.metadata.get('source', 'unknown') for doc in chunks]
    unique_sources = len(set(sources))
    total_chunks = len(chunks)
    
    # Source diversity percentage
    diversity_percentage = (unique_sources / total_chunks) * 100
    return round(diversity_percentage, 2)

def analyze_semantic_overlap():
    """Analyze semantic overlap for NSF queries"""
    
    print("=" * 80)
    print("SEMANTIC OVERLAP ANALYSIS")
    print("=" * 80)
    
    # Initialize
    config = read_yaml_as_dict("src/config.yaml")
    persist_dir = config["chroma"]["persist_directory"]
    embedding_model = get_embedding_model("src/config.yaml")
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedding_model)
    
    # Get all metadata
    try:
        collection = vectordb.get()
        metadatas = collection.get('metadatas', [])
        documents = collection.get('documents', [])
        ids = collection.get('ids', [])
    except Exception as e:
        print(f"Error accessing database: {e}")
        return
    
    if not metadatas:
        print("No data found in database")
        return
    
    # Filter NSF files only
    nsf_data = []
    for i, metadata in enumerate(metadatas):
        if metadata and 'folder' in metadata and 'NSF' in metadata['folder']:
            nsf_data.append({
                'metadata': metadata,
                'content': documents[i] if documents else "",
                'id': ids[i] if ids else i
            })
    
    print(f"NSF documents: {len(nsf_data)}")
    print(f"Total NSF chunks: {len(nsf_data)}")
    print(f"Unique NSF sources: {len(set(item['metadata'].get('source', 'unknown') for item in nsf_data))}")
    
    # Test queries
    test_queries = [
        "New York University high performance computing",
        "COSMOS Wireless Testbed HPC clusters"
    ]
    
    query_results = {}
    
    print("\n" + "=" * 80)
    print("SEMANTIC OVERLAP BY QUERY")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n Query: '{query}'")
        print("-" * 60)
        
        # Get retrieval results for NSF only
        retrieved_docs = search_similar_chunks(query, k=5, selected_types=['NSF'])
        
        if not retrieved_docs:
            print(f" No results found")
            continue
        
        print(f"Retrieved: {len(retrieved_docs)} chunks")
        
        # Calculate semantic overlap
        semantic_overlap = calculate_semantic_overlap(retrieved_docs, embedding_model)
        
        # Calculate source diversity
        source_diversity = calculate_source_diversity(retrieved_docs)
        
        # Get source files
        sources = [doc.metadata.get('source', 'unknown') for doc in retrieved_docs]
        source_counts = Counter(sources)
        
        query_results[query] = {
            'retrieved_count': len(retrieved_docs),
            'unique_sources': len(set(sources)),
            'semantic_overlap': semantic_overlap,
            'source_diversity': source_diversity,
            'sources': sources,
            'source_distribution': dict(source_counts)
        }
        
        print(f"SEMANTIC OVERLAP: {semantic_overlap}%")
        print(f"Source Diversity: {source_diversity}%")
        print(f"Unique Sources: {len(set(sources))}")
        print(f"Source Distribution: {dict(source_counts)}")
        
        # Show chunk previews
        print(f"Chunk Previews:")
        for i, doc in enumerate(retrieved_docs, 1):
            preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
            print(f"    {i}. {preview}")
    
    # FINAL SUMMARY
    print(f"\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    for query, results in query_results.items():
        print(f"'{query}':")
        print(f"  Semantic Overlap: {results['semantic_overlap']}%")
        print(f"  Source Diversity: {results['source_diversity']}%")
        print(f"  Unique Sources: {results['unique_sources']}")
        print()
    
    # Save results
    final_results = {
        'nsf_data_summary': {
            'total_chunks': len(nsf_data),
            'unique_sources': len(set(item['metadata'].get('source', 'unknown') for item in nsf_data))
        },
        'semantic_analysis': {
            query: {
                'retrieved_count': results['retrieved_count'],
                'unique_sources': results['unique_sources'],
                'semantic_overlap': results['semantic_overlap'],
                'source_diversity': results['source_diversity'],
                'sources': results['sources'],
                'source_distribution': results['source_distribution']
            }
            for query, results in query_results.items()
        }
    }
    
    # Save to JSON
    filename = "semantic_overlap_analysis(2).json"
    
    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"Results saved to: {filename}")
    
    return final_results

if __name__ == "__main__":
    analyze_semantic_overlap()
