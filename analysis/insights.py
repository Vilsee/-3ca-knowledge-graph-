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
    print("4. STRONG CROSS-CANCER-TYPE STUDY LINKS (Shared Diseases >= 2)")
    print("-" * 50)
    seen_pairs = set()
    cross_links = []
    
    for u, v, data in G.edges(data=True):
        if data.get('type') == 'SHARES_DISEASE_WITH':
            weight = data.get('weight', 0)
            if weight >= 2:
                pair = tuple(sorted([u, v]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    t_u = G.nodes[u].get('title', '')[:35] + "..." if len(G.nodes[u].get('title', '')) > 35 else G.nodes[u].get('title', '')
                    t_v = G.nodes[v].get('title', '')[:35] + "..." if len(G.nodes[v].get('title', '')) > 35 else G.nodes[v].get('title', '')
                    cross_links.append({
                        "Study 1": u,
                        "Title 1": t_u,
                        "Study 2": v,
                        "Title 2": t_v,
                        "Shared_Diseases": weight
                    })
                    
    df_cross = pd.DataFrame(cross_links)
    if not df_cross.empty:
        df_cross = df_cross.sort_values('Shared_Diseases', ascending=False)
        print(df_cross.to_string(index=False))
        insights["strong_cross_links"] = df_cross.to_dict('records')
    else:
        print("No cross-links with weight >= 2 found.")
        insights["strong_cross_links"] = []
    print("\n")
    
    # 5. Save to JSON
    with open('data/insights_summary.json', 'w') as f:
        json.dump(insights, f, indent=2)
    print("Insights successfully saved to data/insights_summary.json")

if __name__ == '__main__':
    compute_insights()
