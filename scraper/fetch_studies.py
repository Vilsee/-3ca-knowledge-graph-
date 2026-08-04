import time
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

CANCER_SLUGS = [
    "head-and-neck", "lung", "liverbiliary", "kidney",
    "prostate", "sarcoma", "othermodels", "brain", "breast",
    "pancreas", "neuroendocrine", "colorectal", "ovarian", "skin", "hematologic"
]

BASE_URL = "https://www.weizmann.ac.il/sites/3CA/{}"

def get_page(url, retries=1):
    for i in range(retries + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if i < retries:
                time.sleep(1)
            else:
                print(f"Failed to fetch {url}: {e}")
                return None

def extract_study_id(hrefs):
    for href in hrefs:
        if href:
            match = re.search(r'/(\d+)$', href)
            if match:
                return int(match.group(1))
    return None

def parse_int(text):
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text)
    return int(cleaned) if cleaned else None

def extract_author_year(title):
    # e.g., "Bischoff et al. 2021", "Bischoff et al 2021", "Bischoff 2021"
    match = re.search(r'([A-Za-z\-\']+)\s+et\s+al.*?(\d{4})', title, re.IGNORECASE)
    if match:
        return match.group(1), int(match.group(2))
    
    # Fallback to look for a word followed eventually by a 4 digit year
    match = re.search(r'^([A-Za-z\-\']+).*?(20\d{2})', title)
    if match:
        return match.group(1), int(match.group(2))
        
    return None, None

def scrape_3ca():
    all_studies = []
    
    for slug in CANCER_SLUGS:
        url = BASE_URL.format(slug)
        print(f"Scraping {url}...")
        html = get_page(url)
        if not html:
            continue
            
        soup = BeautifulSoup(html, 'lxml')
        
        tables = soup.find_all('table')
        if not tables:
            print(f"  No tables found for {slug}")
            continue
            
        # Target the most likely table (usually the first one with the data)
        target_table = tables[0]
        for table in tables:
            headers = [th.text.strip().lower() for th in table.find_all('th')]
            if 'disease' in headers or 'technology' in headers or '#cells' in headers:
                target_table = table
                break
                
        headers = [th.text.strip() for th in target_table.find_all('th')]
        
        tbody = target_table.find('tbody')
        rows = tbody.find_all('tr') if tbody else target_table.find_all('tr')[1:]
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_text = [cell.text.strip() for cell in cells]
            
            if not cells:
                continue
                
            # Skip summary row
            if any(text.lower().startswith("all ") for text in row_text) and any("cancer" in text.lower() or "model" in text.lower() or slug.lower() in text.lower() for text in row_text):
                continue
                
            all_hrefs = [a.get('href') for a in row.find_all('a') if a.get('href')]
            study_id = extract_study_id(all_hrefs)
            
            title = cells[0].text.strip() if cells else ""
            
            def get_cell_text(keywords):
                for i, h in enumerate(headers):
                    if any(k in h.lower() for k in keywords):
                        return cells[i].text.strip() if i < len(cells) else None
                return None
                
            disease = get_cell_text(["disease"])
            technology = get_cell_text(["tech"])
            samples = parse_int(get_cell_text(["#samples", "samples"]))
            cells_count = parse_int(get_cell_text(["#cells", "cells"]))
            
            author, year = extract_author_year(title)
            
            study = {
                'study_id': study_id,
                'cancer_type': slug,
                'title': title,
                'author': author,
                'year': year,
                'disease': disease,
                'technology': technology,
                'samples': samples,
                'cells': cells_count,
            }
            
            def get_link_by_header(keywords):
                for i, h in enumerate(headers):
                    if any(k in h.lower() for k in keywords):
                        if i < len(cells):
                            a = cells[i].find('a')
                            if a: return a.get('href')
                return None
                
            study['paper_url'] = get_link_by_header(['title']) or (cells[0].find('a').get('href') if cells[0].find('a') else None)
            study['data_url'] = get_link_by_header(['data'])
            study['metadata_url'] = get_link_by_header(['meta-data', 'metadata'])
            study['cell_types_url'] = get_link_by_header(['cell type'])
            study['summary_url'] = get_link_by_header(['summary'])
            study['meta_programs_url'] = get_link_by_header(['meta-program'])
            study['cnas_url'] = get_link_by_header(['cna'])
            study['umap_url'] = get_link_by_header(['umap'])
            study['cell_cycle_url'] = get_link_by_header(['cell cycle'])
            
            # Fallback for URLs by link structure if headers didn't catch them
            for a in row.find_all('a'):
                href = a.get('href')
                if not href: continue
                if 'cell-types' in href: study['cell_types_url'] = href
                if 'summary' in href: study['summary_url'] = href
                if 'meta-programs' in href: study['meta_programs_url'] = href
                if 'cnas' in href: study['cnas_url'] = href
                if 'umap' in href: study['umap_url'] = href
                if 'cell-cycle' in href: study['cell_cycle_url'] = href
            
            all_studies.append(study)
            
        time.sleep(0.5)
        
    df = pd.DataFrame(all_studies)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    out_path = 'data/studies_raw.csv'
    df.to_csv(out_path, index=False)
    print(f"\n--- SCRAPING COMPLETE ---")
    print(f"Saved {len(df)} studies to {out_path}")
    print("\nFirst 5 rows:")
    # Print max columns so it's clearly visible
    pd.set_option('display.max_columns', None)
    print(df.head())

if __name__ == '__main__':
    scrape_3ca()
