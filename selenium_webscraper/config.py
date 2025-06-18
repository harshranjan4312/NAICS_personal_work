from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "scraping_data_enrichment" / "data" / "about_crawl_integrated_20250526_035335.json"

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1

PHRASES = [
    "about us", "who we are", "our mission", "our vision", "our values", "company profile",
    "about our company", "about the company", "our story", "company history", "our history",
    "our background", "vision and mission", "purpose and values", "what we do", "why choose us",
    "meet the team", "leadership team", "management team", "our leadership", "our team",
    "corporate overview", "company overview", "our company", "founders", "from the founder",
    "corporate mission", "corporate vision", "our purpose", "our core values", "our culture",
    "what drives us", "our commitment", "quality and innovation", "sustainability and responsibility",
    "employee spotlight", "who we serve", "customers and partners", "community engagement",
    "corporate responsibility", "board of directors", "executive team", "brand story",
    "our approach", "our goals", "company milestones", "our achievements", "industry expertise",
    "what we do", "what we're doing", "our work", "our services", "our solutions", "how we help",
    "our firm", "our company info", "company information", "firm overview", "our heritage"
]

KEYWORDS = [
    "about", "mission", "vision", "values", "history", "team", "leadership", "story", "company",
    "corporate", "overview", "profile", "purpose", "culture", "commitment", "quality", "innovation",
    "sustainability", "responsibility", "employees", "customers", "partners", "community",
    "expertise", "approach", "goals", "milestones", "achievements"
]

SELENIUM_TIMEOUT = 15
PAGE_LOAD_TIMEOUT = 20
IMPLICIT_WAIT = 10
PROCESS_TIMEOUT_SECONDS = 300

MIN_CONTENT_LENGTH = 50

ABOUT_SECTION_SELECTORS = [
    "section.about",
    "div#about",
    "div[class*='about']",
    "main",
    "article",
    "div.content",
    "div.main-content",
    "div.container"
]

ABOUT_HEADER_PATTERNS = [
    re.compile(r"^\s*About\b", re.IGNORECASE),
    re.compile(r"^\s*Who We Are\b", re.IGNORECASE),
    re.compile(r"^\s*Our Story\b", re.IGNORECASE),
    re.compile(r"^\s*Our Mission\b", re.IGNORECASE),
    re.compile(r"^\s*Our Vision\b", re.IGNORECASE),
    re.compile(r"^\s*Our Values\b", re.IGNORECASE),
    re.compile(r"^\s*Company Profile\b", re.IGNORECASE),
]

ABOUT_URL_KEYWORDS = [
    "about", "who-we-are", "our-story", "mission", "vision", "values", "company-profile",
    "corporate", "history", "team", "leadership", "overview", "philosophy", "purpose",
    "culture", "approach", "goals", "milestones", "achievements"
]

ABOUT_LINK_TEXT_PATTERNS = [
    re.compile(r"about\s*us", re.IGNORECASE),
    re.compile(r"who\s*we\s*are", re.IGNORECASE),
    re.compile(r"our\s*story", re.IGNORECASE),
    re.compile(r"our\s*mission", re.IGNORECASE),
    re.compile(r"our\s*vision", re.IGNORECASE),
    re.compile(r"our\s*values", re.IGNORECASE),
    re.compile(r"company\s*profile", re.IGNORECASE),
    re.compile(r"about", re.IGNORECASE),
    re.compile(r"corporate", re.IGNORECASE),
    re.compile(r"history", re.IGNORECASE),
    re.compile(r"team", re.IGNORECASE),
    re.compile(r"leadership", re.IGNORECASE),
    re.compile(r"overview", re.IGNORECASE),
    re.compile(r"philosophy", re.IGNORECASE),
    re.compile(r"purpose", re.IGNORECASE),
    re.compile(r"culture", re.IGNORECASE),
    re.compile(r"approach", re.IGNORECASE),
    re.compile(r"goals", re.IGNORECASE),
    re.compile(r"milestones", re.IGNORECASE),
    re.compile(r"achievements", re.IGNORECASE),
]

NAV_SELECTORS = [
    "nav",
    "header",
    "footer",
    "ul.main-menu",
    "ul.navigation",
    "div.menu",
    "div[role='navigation']"
]

MAX_ABOUT_PATHS = 10

IRRELEVANT_KEYWORDS = [
    "careers", "jobs", "news", "blog", "investors", "press", "media", "contact", "support",
    "faq", "products", "services", "solutions", "partners", "customers", "client", "privacy",
    "terms", "legal", "cookies", "sitemap", "login", "signin", "register", "cart", "shop",
    "store", "ecommerce", "price", "pricing", "subscribe", "forum", "community", "event",
    "events", "webinar", "webinars", "download", "downloads", "brochure", "whitepaper",
    "case study", "testimonials", "feedback"
]

CLASSIFICATION_WEIGHTS = {
    "min_content_length_met": 1.5, 
    "has_about_section": 1.5,      
    "has_about_link": 0.5,
    "phrase_match": 0.7,            
    "keyword_match": 0.3,           
    "irrelevant_keyword_penalty": -0.5, 
    "url_contains_about": 0.7     
}

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
}

BATCH_SIZE = 50
REQUEST_DELAY_SECONDS = 5
BATCH_DELAY_SECONDS = 60