import pandas as pd
import numpy as np
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_df = None
_tfidf = None
_tfidf_matrix = None

def _load_data():
    global _df, _tfidf, _tfidf_matrix
    if _df is not None:
        return
        
    _df = pd.read_csv('data/studies_clean.csv')
    
    def parse_list(x):
        try:
            return ast.literal_eval(str(x))
        except (ValueError, SyntaxError):
            return []
            
    _df['diseases_list'] = _df['diseases'].apply(parse_list)
    _df['cancer_types_list'] = _df['cancer_types'].apply(parse_list)
    
    # Build a comprehensive text field for TF-IDF
    def build_text(row):
        parts = [
            str(row.get('title', '')),
            str(row.get('author', '')),
            " ".join(row['diseases_list']),
            " ".join(row['cancer_types_list']),
            str(row.get('technology', ''))
        ]
        return " ".join(parts).lower()
        
    _df['search_text'] = _df.apply(build_text, axis=1)
    
    _tfidf = TfidfVectorizer(stop_words='english')
    _tfidf_matrix = _tfidf.fit_transform(_df['search_text'])

def search(query: str, top_k=10):
    """
    Returns a ranked list of studies with cosine similarity scores.
    """
    _load_data()
    
    query_vec = _tfidf.transform([query.lower()])
    sim_scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    
    top_indices = sim_scores.argsort()[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        score = sim_scores[idx]
        if score > 0:
            study = _df.iloc[idx]
            results.append({
                'study_id': int(study['study_id']),
                'title': study['title'],
                'score': float(score)
            })
            
    return results

def filter_studies(cancer_type=None, technology=None, disease_contains=None, min_cells=None):
    """
    Plain metadata filter returning a DataFrame.
    """
    _load_data()
    
    mask = pd.Series([True] * len(_df), index=_df.index)
    
    if cancer_type:
        mask &= _df['cancer_types_list'].apply(lambda x: any(cancer_type.lower() in ct.lower() for ct in x))
        
    if technology:
        mask &= _df['technology'].str.lower() == technology.lower()
        
    if disease_contains:
        mask &= _df['diseases_list'].apply(lambda x: any(disease_contains.lower() in d.lower() for d in x))
        
    if min_cells is not None:
        mask &= _df['cells'] >= min_cells
        
    return _df[mask].copy()

if __name__ == '__main__':
    print("=========================================")
    print("      SEARCH & FILTER TESTING ENGINE     ")
    print("=========================================\n")
    
    print("1. Testing Keyword/Semantic Search for '10x breast cancer':")
    print("-" * 50)
    res = search("10x breast cancer", top_k=5)
    if not res:
        print("  No results found.")
    for r in res:
        print(f"  [{r['score']:.4f}] {r['title']} (ID: {r['study_id']})")
        
    print("\n2. Testing Filter for cancer_type='lung', min_cells=50000:")
    print("-" * 50)
    f_res = filter_studies(cancer_type="lung", min_cells=50000)
    print(f"  Found {len(f_res)} matching studies.")
    if len(f_res) > 0:
        for _, row in f_res.head(5).iterrows():
            print(f"    - ID {int(row['study_id'])} | {row['title']} | Cells: {int(row['cells'])}")
