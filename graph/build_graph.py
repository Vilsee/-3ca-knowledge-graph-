import pandas as pd
import networkx as nx
import ast
import pickle

def build_graph():
    df = pd.read_csv('data/studies_clean.csv')
    
    # Parse list columns safely
    def parse_list(x):
        try:
            return ast.literal_eval(str(x))
        except (ValueError, SyntaxError):
            return []
            
    df['diseases'] = df['diseases'].apply(parse_list)
    df['cancer_types'] = df['cancer_types'].apply(parse_list)
    
    G = nx.DiGraph()
    
    for _, row in df.iterrows():
        study_id = f"study_{int(row['study_id'])}"
        
        # 1. Add Study node
        # We fill NaNs to be Gephi/GraphML compatible (GraphML doesn't support NaNs easily)
        n_samples = float(row['samples']) if not pd.isna(row['samples']) else 0.0
        n_cells = float(row['cells']) if not pd.isna(row['cells']) else 0.0
        year = int(row['year']) if not pd.isna(row['year']) else 0
        
        G.add_node(
            study_id,
            type="Study",
            title=str(row['title']) if pd.notna(row['title']) else "",
            author=str(row['author']) if pd.notna(row['author']) else "",
            year=year,
            n_samples=n_samples,
            n_cells=n_cells,
            data_completeness=float(row['data_completeness'])
        )
        
        # 2. Add CancerType nodes & edges
        for ct in row['cancer_types']:
            ct_id = f"cancertype_{ct}"
            if not G.has_node(ct_id):
                G.add_node(ct_id, type="CancerType")
            G.add_edge(study_id, ct_id, type="STUDIES_CANCER_TYPE")
            
        # 3. Add Disease nodes & edges
        for d in row['diseases']:
            d_id = f"disease_{d}"
            if not G.has_node(d_id):
                G.add_node(d_id, type="Disease")
            G.add_edge(study_id, d_id, type="HAS_DISEASE")
            
        # 4. Add Technology nodes & edges
        tech = row['technology']
        if pd.notna(tech):
            tech_id = f"tech_{tech}"
            if not G.has_node(tech_id):
                G.add_node(tech_id, type="Technology")
            G.add_edge(study_id, tech_id, type="USES_TECH")
            
    # 5. Add SHARES_DISEASE_WITH edges
    studies = df.to_dict('records')
    for i in range(len(studies)):
        for j in range(i + 1, len(studies)):
            s1 = studies[i]
            s2 = studies[j]
            
            ct1 = set(s1['cancer_types'])
            ct2 = set(s2['cancer_types'])
            
            # If they belong to DIFFERENT cancer types (no intersection)
            if ct1.isdisjoint(ct2):
                d1 = set(s1['diseases'])
                d2 = set(s2['diseases'])
                
                shared_diseases = d1.intersection(d2)
                if len(shared_diseases) > 0:
                    sid1 = f"study_{int(s1['study_id'])}"
                    sid2 = f"study_{int(s2['study_id'])}"
                    weight = len(shared_diseases)
                    
                    # Add bi-directional edges for DiGraph
                    G.add_edge(sid1, sid2, type="SHARES_DISEASE_WITH", weight=weight)
                    G.add_edge(sid2, sid1, type="SHARES_DISEASE_WITH", weight=weight)
                    
    # Metrics
    nodes_by_type = {}
    for n, data in G.nodes(data=True):
        t = data.get('type', 'Unknown')
        nodes_by_type[t] = nodes_by_type.get(t, 0) + 1
        
    edges_by_type = {}
    for u, v, data in G.edges(data=True):
        t = data.get('type', 'Unknown')
        edges_by_type[t] = edges_by_type.get(t, 0) + 1
        
    # Centrality
    centrality = nx.degree_centrality(G)
    study_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Study']
    study_centrality = {n: centrality[n] for n in study_nodes}
    top_10_studies = sorted(study_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("--- Graph Build Summary ---")
    print("Nodes by type:")
    for k, v in nodes_by_type.items():
        print(f"  {k}: {v}")
        
    print("\nEdges by type:")
    for k, v in edges_by_type.items():
        print(f"  {k}: {v}")
        
    print("\nTop 10 Studies by Degree Centrality:")
    for n, score in top_10_studies:
        title = G.nodes[n].get('title', 'Unknown')
        print(f"  - {n} ({title[:40]}...): {score:.4f}")
        
    # Save graph
    nx.write_graphml(G, 'data/kg.graphml')
    with open('data/kg.gpickle', 'wb') as f:
        pickle.dump(G, f)
        
    print("\nGraph successfully saved to data/kg.graphml and data/kg.gpickle")

if __name__ == '__main__':
    build_graph()
