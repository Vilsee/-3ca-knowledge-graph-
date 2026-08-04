import streamlit as st
import pandas as pd
import json
import pickle
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import sys
import os

# Add root directory to python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis.search import search, filter_studies

st.set_page_config(page_title="3CA Knowledge Graph", layout="wide")
st.title("🧬 3CA Knowledge Graph")

@st.cache_data
def load_insights():
    try:
        with open('data/insights_summary.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@st.cache_resource
def load_graph():
    with open('data/kg.gpickle', 'rb') as f:
        return pickle.load(f)

@st.cache_data
def load_df():
    return pd.read_csv('data/studies_clean.csv')

insights = load_insights()
G = load_graph()
df_clean = load_df()

tab1, tab2, tab3 = st.tabs(["Explore", "Search", "Graph"])

with tab1:
    st.header("Explore Studies")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        c1, c2 = st.columns(2)
        cancer_type = c1.text_input("Cancer Type (e.g., lung, breast)")
        technology = c2.text_input("Technology (e.g., 10x, SmartSeq2)")
        disease = c1.text_input("Disease Substring")
        min_cells = c2.number_input("Minimum Cells", min_value=0, value=0, step=1000)
        
        if st.button("Apply Filters"):
            filtered_df = filter_studies(
                cancer_type=cancer_type if cancer_type else None,
                technology=technology if technology else None,
                disease_contains=disease if disease else None,
                min_cells=min_cells if min_cells > 0 else None
            )
            st.write(f"Found {len(filtered_df)} studies.")
            cols = ['study_id', 'title', 'cancer_types', 'diseases', 'technology', 'cells']
            # Only show available columns
            cols = [c for c in cols if c in filtered_df.columns]
            st.dataframe(filtered_df[cols])
            
    with col2:
        st.subheader("💡 Insights")
        st.write("**Top Cross-Cancer Links:**")
        cross_links = insights.get("strong_cross_links", [])
        if not cross_links:
            st.info("No strong cross-cancer links (sharing >= 2 diseases) found in this snapshot.")
        else:
            for link in cross_links[:5]:
                s1_id = str(link.get('Study 1', '')).replace('study_', '')
                s2_id = str(link.get('Study 2', '')).replace('study_', '')
                weight = link.get('Shared_Diseases', 0)
                st.write(f"🔹 **Study {s1_id}** and **Study {s2_id}** share {weight} disease subtypes.")

with tab2:
    st.header("Search")
    query = st.text_input("Semantic / Keyword Search (e.g., '10x breast cancer')")
    top_k = st.slider("Results to show", 1, 50, 10)
    
    if query:
        results = search(query, top_k=top_k)
        if results:
            st.write(f"Top {len(results)} results:")
            res_df = pd.DataFrame(results)
            display_df = pd.merge(res_df, df_clean, on='study_id', how='left')
            cols = ['score', 'title_x', 'author', 'year', 'cancer_types', 'diseases', 'technology']
            display_df = display_df[cols].rename(columns={'title_x': 'title'})
            st.dataframe(display_df)
        else:
            st.write("No results found.")

with tab3:
    st.header("Knowledge Graph")
    show_full = st.checkbox("Show full graph (Warning: Dense!)", value=False)
    
    if st.button("Render Graph"):
        with st.spinner("Rendering graph..."):
            nodes_to_keep = []
            centrality = nx.degree_centrality(G)
            
            for n, data in G.nodes(data=True):
                ntype = data.get('type')
                if show_full:
                    nodes_to_keep.append(n)
                else:
                    if ntype in ['CancerType', 'Disease']:
                        nodes_to_keep.append(n)
                    elif ntype == 'Study':
                        if G.degree(n) >= 2:
                            nodes_to_keep.append(n)
                            
            subG = G.subgraph(nodes_to_keep)
            net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)
            
            color_map = {
                'Study': '#1f78b4',
                'CancerType': '#e31a1c',
                'Disease': '#33a02c',
                'Technology': '#ff7f00'
            }
            
            for n, data in subG.nodes(data=True):
                ntype = data.get('type', 'Unknown')
                color = color_map.get(ntype, '#999999')
                
                size = 10
                if ntype == 'Study':
                    cent = centrality.get(n, 0)
                    size = 10 + (cent * 300) 
                    
                label = str(n).replace('study_', '').replace('cancertype_', '').replace('disease_', '').replace('tech_', '')
                title_hover = data.get('title', str(n))
                
                net.add_node(n, label=label[:20], title=title_hover, color=color, size=size)
                
            for u, v, edata in subG.edges(data=True):
                net.add_edge(u, v, title=edata.get('type', ''))
                
            if show_full:
                net.toggle_physics(False)
                
            path = "data/graph_render.html"
            net.save_graph(path)
            with open(path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            components.html(source_code, height=650)
