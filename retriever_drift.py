

import json
import numpy as np
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from langchain.vectorstores import Chroma
from src.utils import get_embedding_model, read_yaml_as_dict
from src.retriever import search_similar_chunks

def calculate_jaccard_similarity(set_a, set_b):
    """Calculate Jaccard similarity between two sets"""
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / max(1, union) 

def calculate_id_stability(runs):
    """Calculate ID stability using Jaccard similarity across all run pairs"""
    jaccard_scores = []
    
    for a in range(len(runs)):
        for b in range(a + 1, len(runs)):

            ids_a = {f"{doc.metadata.get('source', 'unknown')}_{doc.metadata.get('page', 0)}_{hash(doc.page_content[:100])}" for doc in runs[a]}
            ids_b = {f"{doc.metadata.get('source', 'unknown')}_{doc.metadata.get('page', 0)}_{hash(doc.page_content[:100])}" for doc in runs[b]}
            
            jaccard = calculate_jaccard_similarity(ids_a, ids_b)
            jaccard_scores.append(jaccard)
    
    if not jaccard_scores:
        return 0.0
    
    stability = 100 * np.mean(jaccard_scores)
    return round(stability, 2)

def calculate_source_stability(runs):
    """Calculate source stability using Jaccard similarity across all run pairs"""
    jaccard_scores = []
    
    for a in range(len(runs)):
        for b in range(a + 1, len(runs)):
            # Get source files from each run
            sources_a = {doc.metadata.get('source', 'unknown') for doc in runs[a]}
            sources_b = {doc.metadata.get('source', 'unknown') for doc in runs[b]}
            
            jaccard = calculate_jaccard_similarity(sources_a, sources_b)
            jaccard_scores.append(jaccard)
    
    if not jaccard_scores:
        return 0.0
    
    stability = 100 * np.mean(jaccard_scores)
    return round(stability, 2)

def calculate_cross_run_content_stability(runs, embedding_model):
    """Calculate cross-run content stability using cosine similarity"""
    if len(runs) < 2:
        return 100.0
    
    try:
        print("  Calculating embeddings for cross-run content stability...")
        
        # Get embeddings for all chunks across all runs
        all_embeddings = []
        run_boundaries = []  # Track where each run starts/ends
        
        start_idx = 0
        for run_idx, run in enumerate(runs):
            run_embeddings = []
            for chunk_idx, doc in enumerate(run):
                embedding = embedding_model.embed_query(doc.page_content)
                all_embeddings.append(embedding)
                run_embeddings.append(embedding)
            
            run_boundaries.append((start_idx, start_idx + len(run_embeddings)))
            start_idx += len(run_embeddings)
        
        # Convert to numpy array
        embeddings_array = np.array(all_embeddings)
        
        # Calculate pairwise similarities between all runs
        cross_run_similarities = []
        
        for a in range(len(runs)):
            for b in range(a + 1, len(runs)):
                start_a, end_a = run_boundaries[a]
                start_b, end_b = run_boundaries[b]
                
                # Get embeddings for run a and run b
                run_a_embeddings = embeddings_array[start_a:end_a]
                run_b_embeddings = embeddings_array[start_b:end_b]
                
                # Calculate cosine similarity between the two runs
                similarity_matrix = cosine_similarity(run_a_embeddings, run_b_embeddings)
                
                # Take the mean of all pairwise similarities
                avg_similarity = np.mean(similarity_matrix)
                cross_run_similarities.append(avg_similarity)
        
        if not cross_run_similarities:
            return 100.0
        
        stability = 100 * np.mean(cross_run_similarities)
        return round(stability, 2)
        
    except Exception as e:
        print(f"  Error calculating cross-run content stability: {e}")
        return 0.0

def calculate_improved_retriever_drift(query, num_runs=5, k=5, selected_types=['NSF']):
    """Calculate retriever drift using valid metrics"""
    
    print(f" Running query '{query}' {num_runs} times...")
    
    # Store results from each run
    runs = []
    
    for run in range(num_runs):
        print(f"  Run {run + 1}/{num_runs}...")
        
        # Get retrieval results
        retrieved_docs = search_similar_chunks(query, k=k, selected_types=selected_types)
        
        if not retrieved_docs:
            print(f"    No results in run {run + 1}")
            continue
        
        runs.append(retrieved_docs)
        print(f"    Retrieved {len(retrieved_docs)} chunks")
    
    if len(runs) < 2:
        return {
            'id_stability': 0.0,
            'id_drift': 100.0,
            'source_stability': 0.0,
            'source_drift': 100.0,
            'content_stability': 0.0,
            'content_drift': 100.0,
            'total_runs': num_runs,
            'successful_runs': len(runs)
        }
    
    # Calculate the three drift metrics
    id_stability = calculate_id_stability(runs)
    source_stability = calculate_source_stability(runs)
    
    # Calculate content stability
    embedding_model = get_embedding_model("src/config.yaml")
    content_stability = calculate_cross_run_content_stability(runs, embedding_model)
    
    # Calculate drift percentages (inverse of stability)
    id_drift = 100 - id_stability
    source_drift = 100 - source_stability
    content_drift = 100 - content_stability
    
    return {
        'id_stability': id_stability,
        'id_drift': round(id_drift, 2),
        'source_stability': source_stability,
        'source_drift': round(source_drift, 2),
        'content_stability': content_stability,
        'content_drift': round(content_drift, 2),
        'total_runs': num_runs,
        'successful_runs': len(runs),
        'runs_data': runs
    }

def analyze_improved_retriever_drift():
    """Analyze retriever drift using valid metrics"""
    
    print("=" * 80)
    print("IMPROVED RETRIEVER DRIFT ANALYSIS")
    print("=" * 80)
    print("Using valid drift metrics: ID stability, source stability, content stability...")
    
    # Initialize
    config = read_yaml_as_dict("src/config.yaml")
    persist_dir = config["chroma"]["persist_directory"]
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=get_embedding_model("src/config.yaml"))
    
    # Get NSF data summary
    try:
        collection = vectordb.get()
        metadatas = collection.get('metadatas', [])
        nsf_data = []
        for i, metadata in enumerate(metadatas):
            if metadata and 'folder' in metadata and 'NSF' in metadata['folder']:
                nsf_data.append(metadata)
    except Exception as e:
        print(f"Error accessing database: {e}")
        return
    
    print(f"NSF documents: {len(nsf_data)}")
    print(f"Total NSF chunks: {len(nsf_data)}")
    print(f"Unique NSF sources: {len(set(item.get('source', 'unknown') for item in nsf_data))}")
    
    # Test queries
    test_queries = [
        "New York University high performance computing",
        "COSMOS Wireless Testbed HPC clusters"
    ]
    
    drift_results = {}
    
    print("\n" + "=" * 80)
    print("DRIFT ANALYSIS BY QUERY")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n Query: '{query}'")
        print("-" * 60)
        
        # Calculate drift for this query
        drift_data = calculate_improved_retriever_drift(query, num_runs=5, k=5, selected_types=['NSF'])
        
        drift_results[query] = drift_data
        
        # Display results
        print(f"ID STABILITY: {drift_data['id_stability']}%")
        print(f"ID DRIFT: {drift_data['id_drift']}%")
        print(f"SOURCE STABILITY: {drift_data['source_stability']}%")
        print(f"SOURCE DRIFT: {drift_data['source_drift']}%")
        print(f"CONTENT STABILITY: {drift_data['content_stability']}%")
        print(f"CONTENT DRIFT: {drift_data['content_drift']}%")
        print(f"Successful Runs: {drift_data['successful_runs']}/{drift_data['total_runs']}")
        
        # Show run-by-run analysis
        print(f"Run-by-Run Analysis:")
        for i, run_data in enumerate(drift_data['runs_data']):
            sources = [doc.metadata.get('source', 'unknown') for doc in run_data]
            print(f"  Run {i+1}: {len(run_data)} chunks, Sources: {sources}")
    
    # FINAL SUMMARY
    print(f"\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    for query, results in drift_results.items():
        print(f"'{query}':")
        print(f"  ID Drift: {results['id_drift']}%")
        print(f"  Source Drift: {results['source_drift']}%")
        print(f"  Content Drift: {results['content_drift']}%")
        print()
    
    # Save results
    final_results = {
        'nsf_data_summary': {
            'total_chunks': len(nsf_data),
            'unique_sources': len(set(item.get('source', 'unknown') for item in nsf_data))
        },
        'improved_drift_analysis': {
            query: {
                'id_stability': results['id_stability'],
                'id_drift': results['id_drift'],
                'source_stability': results['source_stability'],
                'source_drift': results['source_drift'],
                'content_stability': results['content_stability'],
                'content_drift': results['content_drift'],
                'successful_runs': results['successful_runs'],
                'total_runs': results['total_runs']
            }
            for query, results in drift_results.items()
        }
    }
    
    # Save to JSON
    filename = "retriever_drift_analysis(2).json"
    
    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"Results saved to: {filename}")
    
    return final_results

if __name__ == "__main__":
    analyze_improved_retriever_drift()
