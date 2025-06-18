import re
from bs4 import BeautifulSoup

def has_about_link(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    for nav in soup.find_all(['nav', 'header', 'ul']):
        for a in nav.find_all('a', href=True):
            if 'about' in a['href'].lower():
                return True
    return False

def has_about_section(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one('section.about, div#about, div[class*=about]'):
        return True
    for h in soup.find_all(re.compile('^h[1-6]$')):
        if re.match(r'^\s*About\b', h.get_text(strip=True), re.IGNORECASE):
            return True
    return False