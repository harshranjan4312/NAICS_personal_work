import json
from collections import Counter
from pathlib import Path
from config import DATA_PATH
from load_data import load_businesses

def analyze_businesses():
    print("\n=== ANALYZING BUSINESS DATA ===")
    
    businesses = load_businesses()
    total = len(businesses)
    print(f"Total businesses: {total}")
    
    categories = {
        'has_content': [],
        'has_url_no_content': [],
        'no_url_no_content': [],
        'no_url_has_content': []
    }
    
    url_patterns = Counter()
    
    for biz in businesses:
        has_url = bool(biz.web_url and biz.web_url.strip())
        has_content = bool(biz.combined_text and biz.combined_text.strip())
        
        if has_content:
            if has_url:
                categories['has_content'].append(biz)
            else:
                categories['no_url_has_content'].append(biz)
        else:
            if has_url:
                categories['has_url_no_content'].append(biz)
            else:
                categories['no_url_no_content'].append(biz)
        
        if biz.web_url:
            url = biz.web_url.strip().lower()
            if url.startswith(('http://', 'https://')):
                url_patterns['full_url'] += 1
            elif '.' in url and len(url) > 4:
                url_patterns['partial_url'] += 1
            elif url in ['n/a', 'na', 'none', '-', '']:
                url_patterns['placeholder'] += 1
            else:
                url_patterns['other'] += 1
    
    print(f"\n=== CATEGORY BREAKDOWN ===")
    print(f"Has URL + Has Content: {len(categories['has_content'])} ({len(categories['has_content'])/total*100:.1f}%)")
    print(f"Has URL + No Content: {len(categories['has_url_no_content'])} ({len(categories['has_url_no_content'])/total*100:.1f}%)")
    print(f"No URL + No Content: {len(categories['no_url_no_content'])} ({len(categories['no_url_no_content'])/total*100:.1f}%)")
    print(f"No URL + Has Content: {len(categories['no_url_has_content'])} ({len(categories['no_url_has_content'])/total*100:.1f}%)")
    
    print(f"\n=== URL PATTERNS ===")
    for pattern, count in url_patterns.most_common():
        print(f"{pattern}: {count}")
    
    print(f"\n=== SCRAPING CANDIDATES ===")
    print(f"Businesses that CAN be scraped (has URL, no content): {len(categories['has_url_no_content'])}")
    print(f"Businesses that NEED URL discovery (no URL): {len(categories['no_url_no_content'])}")
    
    print(f"\n=== SAMPLE: Has URL but No Content (first 10) ===")
    for i, biz in enumerate(categories['has_url_no_content'][:10], 1):
        print(f"{i}. {biz.company_name[:40]:40} | {biz.web_url}")
    
    print(f"\n=== SAMPLE: No URL at all (first 10) ===")
    for i, biz in enumerate(categories['no_url_no_content'][:10], 1):
        print(f"{i}. {biz.company_name[:40]:40} | Industry: {biz.naics_1_title or 'N/A'}")
    
    output_file = 'businesses_with_urls_no_content.json'
    with open(output_file, 'w') as f:
        data = []
        for biz in categories['has_url_no_content']:
            data.append({
                '_id': biz._id,
                'company_name': biz.company_name,
                'web_url': biz.web_url,
                'combined_text': biz.combined_text or ''
            })
        json.dump(data, f, indent=2)
    
    print(f"\n=== OUTPUT ===")
    print(f"Saved {len(categories['has_url_no_content'])} businesses with URLs but no content to: {output_file}")
    
    return categories

if __name__ == '__main__':
    analyze_businesses()