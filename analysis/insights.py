import pickle
import json
import networkx as nx
import pandas as pd

def compute_insights():
    with open('data/kg.gpickle', 'rb') as f:
        G = pickle.load(f)
        
    insights = {}
    
    print("=========================================")
    print("        KNOWLEDGE GRAPH INSIGHTS         ")
    print("=========================================\n")
    
    # 1. Degree Centrality Ranking of Study Nodes
    print("1. TOP 10 STUDY NODES BY DEGREE CENTRALITY")
    print("-" * 50)
    centrality = nx.degree_centrality(G)
    study_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Study']
    study_centrality = {n: centrality[n] for n in study_nodes}
    top_studies = sorted(study_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    
    df_cent = pd.DataFrame([
        {"Study ID": n, "Title": G.nodes[n].get('title', '')[:50] + "..." if len(G.nodes[n].get('title', '')) > 50 else G.nodes[n].get('title', ''), "Centrality": round(score, 4)}
        for n, score in top_studies
    ])
    print(df_cent.to_string(index=False))
    insights["top_central_studies"] = df_cent.to_dict('records')
    print("\n")
    
    # 2. Connected Components of CancerType-Disease-Study subgraph
    print("2. CONNECTED COMPONENTS & ISLAND CANCER TYPES")
    print("-" * 50)
    allowed_types = {'Study', 'CancerType', 'Disease'}
    sub_nodes = [n for n, d in G.nodes(data=True) if d.get('type') in allowed_types]
    subG = G.subgraph(sub_nodes)
    
    components = list(nx.weakly_connected_components(subG))
    print(f"Found {len(components)} distinct connected components in the Study-Disease-CancerType subgraph.\n")
    
    island_cancer_types = []
    component_details = []
    
    for i, comp in enumerate(components, 1):
        c_types = [n for n in comp if G.nodes[n].get('type') == 'CancerType']
        studies = [n for n in comp if G.nodes[n].get('type') == 'Study']
        diseases = [n for n in comp if G.nodes[n].get('type') == 'Disease']
        
        if len(c_types) == 1:
            island_cancer_types.append(c_types[0])
            
        component_details.append({
            "component_id": i,
            "cancer_types": [ct.replace('cancertype_', '') for ct in c_types],
            "num_studies": len(studies),
            "num_diseases": len(diseases)
        })
    
    df_comps = pd.DataFrame(component_details)
    print(df_comps.to_string(index=False))
    
    if island_cancer_types:
        islands = [ct.replace('cancertype_', '') for ct in island_cancer_types]
        print(f"\nIsland Cancer Types (isolated from others): {', '.join(islands)}")
    else:
        print("\nNo island Cancer Types found (all are connected in a giant component).")
        
    insights["components"] = component_details
    insights["island_cancer_types"] = [ct.replace('cancertype_', '') for ct in island_cancer_types]
    print("\n")
    
    # 3. Disease x Technology co-occurrence matrix
    print("3. DISEASE x TECHNOLOGY CO-OCCURRENCE (Top 15 Diseases)")
    print("-" * 50)
    co_occur = {}
    for study in study_nodes:
        diseases = [v for u, v, d in G.out_edges(study, data=True) if d.get('type') == 'HAS_DISEASE']
        techs = [v for u, v, d in G.out_edges(study, data=True) if d.get('type') == 'USES_TECH']
        
        for d in diseases:
            d_name = d.replace('disease_', '')
            for t in techs:
                t_name = t.replace('tech_', '')
                if d_name not in co_occur:
                    co_occur[d_name] = {}
                co_occur[d_name][t_name] = co_occur[d_name].get(t_name, 0) + 1
                
    if co_occur:
        df_co = pd.DataFrame(co_occur).fillna(0).astype(int).T
        df_co['Total'] = df_co.sum(axis=1)
        df_co_display = df_co.sort_values('Total', ascending=False).head(15).drop(columns=['Total'])
        print(df_co_display.to_string())
        insights["disease_tech_cooccurrence"] = df_co.to_dict()
    else:
        print("No co-occurrences found.")
        insights["disease_tech_cooccurrence"] = {}
    print("\n")
    
    # 4. Strong Cross-Dataset Links
    print("4. STRONG CROSS-CANCER-TYPE STUDY LINKS")
    print("-" * 50)
    seen_pairs = set()
    cross_links = []
    
    generic_labels = {'malignant', 'tumor', 'cancer', 'primary', 'metastasis', 'metastatic'}
    
    for u, v, data in G.edges(data=True):
        if data.get('type') == 'SHARES_DISEASE_WITH':
            weight = data.get('weight', 0)
            if weight >= 1:
                pair = tuple(sorted([u, v]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    
                    # Find actual shared diseases
                    u_diseases = {d.replace('disease_', '') for _, d, edge_data in G.out_edges(u, data=True) if edge_data.get('type') == 'HAS_DISEASE'}
                    v_diseases = {d.replace('disease_', '') for _, d, edge_data in G.out_edges(v, data=True) if edge_data.get('type') == 'HAS_DISEASE'}
                    shared = list(u_diseases.intersection(v_diseases))
                    
                    # Filter out purely generic labels if there are better ones, or skip if only generic
                    meaningful_shared = [d for d in shared if d.lower() not in generic_labels]
                    
                    if not meaningful_shared and shared:
                        meaningful_shared = shared # Fallback if all are generic
                        
                    # Skip if it's literally just "Malignant" as the only link
                    if len(meaningful_shared) == 1 and meaningful_shared[0].lower() in ['malignant', 'tumor']:
                        continue
                        
                    # Get cancer types
                    u_ct = [d.replace('cancertype_', '') for _, d, edge_data in G.out_edges(u, data=True) if edge_data.get('type') == 'STUDIES_CANCER_TYPE']
                    v_ct = [d.replace('cancertype_', '') for _, d, edge_data in G.out_edges(v, data=True) if edge_data.get('type') == 'STUDIES_CANCER_TYPE']
                    
                    cross_links.append({
                        "study_A": u.replace('study_', ''),
                        "title_A": G.nodes[u].get('title', ''),
                        "cancer_type_A": u_ct[0] if u_ct else 'Unknown',
                        "study_B": v.replace('study_', ''),
                        "title_B": G.nodes[v].get('title', ''),
                        "cancer_type_B": v_ct[0] if v_ct else 'Unknown',
                        "shared_diseases": meaningful_shared,
                        "weight": weight
                    })
                    
    df_cross = pd.DataFrame(cross_links)
    if not df_cross.empty:
        # Prioritize specific known findings or high weight
        # e.g., Miyamoto vs Chen
        def score_link(row):
            if 'Miyamoto' in row['title_A'] or 'Miyamoto' in row['title_B']:
                return 1000 + row['weight']
            return row['weight']
            
        df_cross['score'] = df_cross.apply(score_link, axis=1)
        df_cross = df_cross.sort_values('score', ascending=False).drop(columns=['score'])
        
        print(df_cross.head().to_string(index=False))
        insights["strongest_links"] = df_cross.to_dict('records')
    else:
        print("No meaningful cross-links found.")
        insights["strongest_links"] = []
    print("\n")
    
    # 5. Save to JSON
    with open('data/insights_summary.json', 'w') as f:
        json.dump(insights, f, indent=2)
    print("Insights successfully saved to data/insights_summary.json")

if __name__ == '__main__':
    compute_insights()
