import asyncio
import re
from config import (
    PHRASES,
    KEYWORDS,
    IRRELEVANT_KEYWORDS,
    CLASSIFICATION_WEIGHTS,
    MIN_CONTENT_LENGTH,
    ABOUT_SECTION_SELECTORS,
    ABOUT_HEADER_PATTERNS,
    ABOUT_URL_KEYWORDS
)
from html_detection import has_about_section, has_about_link
from urllib.parse import urlparse

IRRELEVANT_PATTERNS = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in IRRELEVANT_KEYWORDS]
ABOUT_URL_PATTERNS = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in ABOUT_URL_KEYWORDS]


def calculate_scrape_score(business_data: dict) -> float:
    text = (business_data.get('combined_text') or business_data.get('about_text') or business_data.get('raw_text') or '').strip().lower()
    web_url = business_data.get('web_url', '').lower()
    score = 0.0

    # Check minimum content length
    if len(text) >= MIN_CONTENT_LENGTH:
        score += CLASSIFICATION_WEIGHTS.get("min_content_length_met", 0)

    # Check for about section
    if has_about_section(text):
        score += CLASSIFICATION_WEIGHTS.get("has_about_section", 0)

    # Check for about link
    if has_about_link(text):
        score += CLASSIFICATION_WEIGHTS.get("has_about_link", 0)

    # Check for phrase matches (only count once)
    phrase_found = False
    for phrase in PHRASES:
        if phrase in text:
            phrase_found = True
            break
    if phrase_found:
        score += CLASSIFICATION_WEIGHTS.get("phrase_match", 0)

    # Check for keyword matches (only count once)
    keyword_found = False
    for kw in KEYWORDS:
        if kw in text:
            keyword_found = True
            break
    if keyword_found:
        score += CLASSIFICATION_WEIGHTS.get("keyword_match", 0)

    # Check for irrelevant keywords (penalty)
    for irrelevant_pattern in IRRELEVANT_PATTERNS:
        if irrelevant_pattern.search(text):
            score += CLASSIFICATION_WEIGHTS.get("irrelevant_keyword_penalty", 0)
            break

    # Check if URL contains about keywords
    for url_pattern in ABOUT_URL_PATTERNS:
        if url_pattern.search(web_url):
            score += CLASSIFICATION_WEIGHTS.get("url_contains_about", 0)
            break

    return score


async def is_good_scrape_async(business):
    business_dict = business.__dict__ if hasattr(business, '__dict__') else business
    score = calculate_scrape_score(business_dict)

    # Adjusted threshold - this should be higher to reduce false positives
    GOOD_SCRAPE_THRESHOLD = 2.0  # Increased from 0.5
    
    return score >= GOOD_SCRAPE_THRESHOLD, score


async def find_bad_scrapes(businesses):
    businesses_with_content = []
    empty_count = 0
    
    for business in businesses:
        text_content = (business.combined_text or business.about_text or business.raw_text or '').strip()
        if not text_content:
            empty_count += 1
        else:
            businesses_with_content.append(business)
    
    print(f"Filtered from {len(businesses)} to {len(businesses_with_content)} businesses with content.")
    print(f"Found {empty_count} truly empty businesses (no text content in combined/about/raw).")

    bad_scrapes = []
    good_scrapes = []
    tasks = [is_good_scrape_async(b) for b in businesses_with_content]
    results = await asyncio.gather(*tasks)

    for business, (is_good, score) in zip(businesses_with_content, results):
        business_info = {
            '_id': business._id,
            'company_name': business.company_name,
            'web_url': business.web_url,
            'combined_text_snippet': (business.combined_text[:500] + '...') if business.combined_text else '',
            'score': score,
            'is_good_scrape': is_good
        }
        if not is_good:
            bad_scrapes.append(business_info)
        else:
            good_scrapes.append(business_info)

    return bad_scrapes, good_scrapes, empty_count

def get_bad_scrapes(businesses):
    bad, good, empty = asyncio.run(find_bad_scrapes(businesses))
    return bad, good, empty

if __name__ == '__main__':
    
    class MockBusiness:
        def __init__(self, _id, company_name, web_url, combined_text):
            self._id = _id
            self.company_name = company_name
            self.web_url = web_url
            self.combined_text = combined_text
            self.about_text = None
            self.raw_text = None

    sample_businesses = [
        MockBusiness(
            _id="1", 
            company_name="About Us Corp", 
            web_url="http://www.aboutuscorp.com/about", 
            combined_text="Our mission is to provide innovative solutions. We are a team of dedicated professionals. Our history dates back to 1990."
        ),
        MockBusiness(
            _id="2", 
            company_name="News Co", 
            web_url="http://www.news.com/latest", 
            combined_text="Breaking news: Local event coverage. Read more on our blog. Subscribe for updates. Careers available now."
        ),
        MockBusiness(
            _id="3",
            company_name="Empty Site",
            web_url="http://www.empty.com",
            combined_text=""
        ),
        MockBusiness(
            _id="4",
            company_name="Investor Relations Inc.",
            web_url="http://www.investorrelations.com/investors",
            combined_text="Welcome investors! Check our latest stock information and quarterly reports. Join our shareholder meeting."
        )
    ]
    
    print("Running detection on sample data:")
    bad_scrapes_sample, good_scrapes_sample, empty_count_sample = get_bad_scrapes(sample_businesses)

    print("\n--- Good Scrapes (Sample) ---")
    for b in good_scrapes_sample:
        print(f"ID: {b['_id']}, Name: {b['company_name']}, Score: {b['score']:.2f}")
    
    print("\n--- Bad Scrapes (Sample) ---")
    for b in bad_scrapes_sample:
        print(f"ID: {b['_id']}, Name: {b['company_name']}, Score: {b['score']:.2f}")
    
    print(f"\nTotal empty scrapes in sample: {empty_count_sample}")
