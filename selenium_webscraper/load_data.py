import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from config import DATA_PATH

@dataclass
class Business:
    _id: str
    seq_num: str
    duns_num: str
    duns_status: Optional[str]
    company_name: str
    tradestyle: Optional[str]
    top_contact: Optional[str]
    title: Optional[str]
    street_address: Optional[str]
    phone: Optional[str]
    web_url: Optional[str]
    total_emps: Optional[str]
    emps_on_site: Optional[str]
    sales_volume: Optional[str]
    public_private: Optional[str]
    year_started: Optional[str]
    latitude: Optional[str]
    longtitude: Optional[str]
    naics_1_num: Optional[str]
    naics_1_title: Optional[str]
    naics_2_num: Optional[str]
    naics_2_title: Optional[str]
    sic_1_num: Optional[str]
    sic_1_title: Optional[str]
    sic_2_num: Optional[str]
    sic_2_title: Optional[str]
    number_of_locations: Optional[str]
    date_of_report: Optional[str]
    raw_text: Optional[str]
    about_text: Optional[str]
    combined_text: Optional[str]
    raw_token_count: Optional[int]
    about_token_count: Optional[int]
    combined_token_count: Optional[int]
    error: Optional[str]
    selenium_status: Optional[str] = None
    selenium_scraped_content_length: Optional[int] = None
    selenium_debug_info: Optional[Dict[str, Any]] = None

def load_businesses(path: str = DATA_PATH) -> List[Business]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    businesses = []
    for item in data:
        if 'selenium_status' not in item:
            item['selenium_status'] = None
        if 'selenium_scraped_content_length' not in item:
            item['selenium_scraped_content_length'] = None
        if 'selenium_debug_info' not in item:
            item['selenium_debug_info'] = None
        businesses.append(Business(**item))
    return businesses

def print_all_combined_texts(limit: Optional[int] = None):
    businesses = load_businesses()
    
    if not businesses:
        print("No businesses loaded to display combined_text.")
        return

    display_count = limit if limit is not None else len(businesses)
    print(f"Displaying combined_text for the first {display_count} businesses:")
    print("=" * 80)

    for i, biz in enumerate(businesses[:display_count]):
        print(f"\n--- Business {i+1} ---")
        print(f"Company Name: {biz.company_name}")
        print(f"Web URL: {biz.web_url if biz.web_url else '[N/A]'}")
        print(f"Selenium Status: {biz.selenium_status if biz.selenium_status else '[N/A]'}")
        print(f"Scraped Content Length: {biz.selenium_scraped_content_length if biz.selenium_scraped_content_length is not None else '[N/A]'}")
        print(f"Combined Text Snippet: {biz.combined_text[:200] + '...' if biz.combined_text else '[N/A]'}")
        if biz.selenium_debug_info:
            print(f"Selenium Debug Info Snippet: {str(biz.selenium_debug_info)[:200] + '...'}")
