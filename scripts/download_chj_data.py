import os
import io
import requests
import zipfile
from bs4 import BeautifulSoup
import re
from pathlib import Path

# Paths
BASE_DIR = Path(r"c:\Users\PCSTAR\Desktop\TFM\RAG_BASIC_TEST_LANGCHAIN")
HTML_FILE = BASE_DIR / "chj_utf8.html"
OUT_DIR = BASE_DIR / "backend" / "vault" / "csvs" / "CHJ_OpenData"
WMS_FILE = BASE_DIR / "backend" / "vault" / "CHJ_WMS_Endpoints.md"

import unicodedata

def clean_filename(name):
    # Remove accents/diacritics
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*.]', '_', name) # Also replace dots to avoid weird Windows issues
    name = name.strip()
    # Limit length to avoid Windows MAX_PATH errors
    if len(name) > 30:
        name = name[:30].strip('_').strip()
    return name

def process_li(li_element, current_path, downloads, wms_links):
    texts = [t.strip() for t in li_element.find_all(string=True, recursive=False) if t.strip()]
    if texts:
        category_name = clean_filename(texts[0])
    else:
        category_name = "Misc"
    
    new_path = current_path + [category_name]
    
    # Check for links in this LI (direct children only)
    for a in li_element.find_all('a', recursive=False):
        text = a.get_text(strip=True)
        href = a.get('href', '')
        if text == 'Datos' and '.zip' in href:
            downloads.append((new_path, href))
        elif text == 'WMS':
            wms_links.append((new_path, href))
            
    # Process nested ULs
    for ul in li_element.find_all('ul', recursive=False):
        for child_li in ul.find_all('li', recursive=False):
            process_li(child_li, new_path, downloads, wms_links)

def main():
    print("Fetching HTML from CHJ website...")
    res = requests.get("https://aps.chj.es/down/html/descargas.html")
    html_text = res.content.decode('utf-8', errors='replace')
    soup = BeautifulSoup(html_text, 'html.parser')
        
    downloads = []
    wms_links = []
    
    principal_ul = soup.find('ul', class_='principal')
    if not principal_ul:
        print("Could not find <ul class='principal'>")
        return
        
    for li in principal_ul.find_all('li', recursive=False):
        process_li(li, [], downloads, wms_links)
        
    print(f"Found {len(downloads)} CSV datasets to download.")
    print(f"Found {len(wms_links)} WMS endpoints.")
    
    # Process WMS
    print(f"Writing WMS endpoints to {WMS_FILE}...")
    WMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WMS_FILE, "w", encoding="utf-8") as f:
        f.write("# CHJ WMS Endpoints\n\n")
        f.write("These are live map server endpoints that can be used in a frontend UI (Leaflet, ArcGIS, etc.).\n\n")
        
        last_path = None
        for path, href in wms_links:
            path_str = " > ".join(path)
            if path_str != last_path:
                f.write(f"\n### {path_str}\n")
                last_path = path_str
            f.write(f"- [WMS Endpoint]({href})\n")
            
    # Process Downloads
    print("\nStarting downloads...")
    for i, (path, href) in enumerate(downloads, 1):
        # Create directory
        target_dir = OUT_DIR.joinpath(*path)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[{i}/{len(downloads)}] Downloading {href}...")
        try:
            res = requests.get(href, timeout=60)
            res.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                valid_files = [n for n in z.namelist() if n.lower().endswith(('.csv', '.xlsx'))]
                if not valid_files:
                    print(f"  WARNING: No CSV or XLSX found in {href}")
                for f_name in valid_files:
                    extracted_path = z.extract(f_name, path=target_dir)
                    
                    if f_name.lower().endswith('.xlsx'):
                        try:
                            import pandas as pd
                            df = pd.read_excel(extracted_path)
                            csv_path = str(extracted_path).rsplit('.', 1)[0] + '.csv'
                            df.to_csv(csv_path, index=False, encoding='utf-8')
                            os.remove(extracted_path)
                            print(f"  Converted to CSV: {csv_path}")
                        except Exception as e:
                            print(f"  ERROR converting {f_name} to CSV: {e}")
                    else:
                        print(f"  Extracted: {extracted_path}")
                    
        except Exception as e:
            print(f"  ERROR downloading or extracting {href}: {e}")

    print("\nAll done!")

if __name__ == "__main__":
    main()
