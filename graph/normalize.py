import pandas as pd
import numpy as np

def normalize_data():
    # Load raw data
    df = pd.read_csv('data/studies_raw.csv')
    
    # Drop rows without a valid study_id
    df = df.dropna(subset=['study_id']).copy()
    
    # 1. Split Disease column into a list column
    df['diseases'] = df['disease'].fillna('').apply(
        lambda x: [d.strip() for d in str(x).split(',') if d.strip() and str(x) != 'nan']
    )
    
    # 2. Normalize Technology
    df['technology_raw'] = df['technology']
    
    def norm_tech(t):
        if pd.isna(t):
            return 'Other'
        t_str = str(t).lower()
        if '10x' in t_str:
            return '10x'
        elif 'smartseq2' in t_str or 'smart-seq2' in t_str or 'smartseq' in t_str:
            return 'SmartSeq2'
        elif 'indrop' in t_str:
            return 'inDrop'
        else:
            return 'Other'
            
    df['technology'] = df['technology'].apply(norm_tech)
    
    # 3. Data completeness score
    optional_fields = ['meta_programs_url', 'cnas_url', 'umap_url', 'cell_cycle_url']
    for field in optional_fields:
        if field not in df.columns:
            df[field] = np.nan
            
    def is_valid_url(val):
        if pd.isna(val): return False
        s = str(val).strip()
        return bool(s and s.lower() != 'none')
        
    valid_counts = df[optional_fields].map(is_valid_url).sum(axis=1) if hasattr(df, 'map') else df[optional_fields].applymap(is_valid_url).sum(axis=1)
    df['data_completeness'] = valid_counts / 4.0
    
    # 4. Deduplicate on study_id and merge cancer types
    # Create aggregation dictionary for all columns except study_id and cancer_type
    agg_dict = {col: 'first' for col in df.columns if col not in ['cancer_type', 'study_id']}
    # For cancer_type, collect into a list of unique values
    agg_dict['cancer_type'] = lambda x: list(set(x))
    
    # Group by study_id and aggregate
    merged = df.groupby('study_id').agg(agg_dict).reset_index()
    # Rename cancer_type to cancer_types
    merged.rename(columns={'cancer_type': 'cancer_types'}, inplace=True)
    
    # 5. Save and print summary
    merged.to_csv('data/studies_clean.csv', index=False)
    
    total_unique = len(merged)
    total_cells = merged['cells'].sum()
    tech_breakdown = merged['technology'].value_counts().to_dict()
    multi_cancer = merged[merged['cancer_types'].apply(len) > 1]
    
    print("--- Normalization Summary ---")
    print(f"Total Unique Studies: {total_unique}")
    print(f"Total Cells: {int(total_cells):,}")
    print("\nTechnology Breakdown:")
    for tech, count in tech_breakdown.items():
        print(f"  {tech}: {count}")
    print(f"\nStudies in >1 cancer type: {len(multi_cancer)}")
    if len(multi_cancer) > 0:
        for idx, row in multi_cancer.head(10).iterrows():
            print(f"  - {row['title']} (ID: {int(row['study_id'])}): {', '.join(row['cancer_types'])}")
            
if __name__ == '__main__':
    normalize_data()
