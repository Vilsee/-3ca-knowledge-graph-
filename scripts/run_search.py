import sys
import json
import os

# Ensure the parent directory is in the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from analysis.search import search

if __name__ == '__main__':
    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    # Supress warnings/logs from pandas/sklearn
    import warnings
    warnings.filterwarnings('ignore')
    
    results = search(query, top_k=top_k)
    print(json.dumps(results))
