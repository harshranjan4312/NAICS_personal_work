import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urlunparse
import multiprocessing
import sys
from pathlib import Path

from config import (
    PHRASES, KEYWORDS, ABOUT_URL_KEYWORDS, ABOUT_LINK_TEXT_PATTERNS,
    ABOUT_SECTION_SELECTORS, NAV_SELECTORS,
    SELENIUM_TIMEOUT, PAGE_LOAD_TIMEOUT, IMPLICIT_WAIT,
    MIN_CONTENT_LENGTH, MAX_ABOUT_PATHS, PROCESS_TIMEOUT_SECONDS,IRRELEVANT_KEYWORDS
)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup not found. Please install it: pip install beautifulsoup4", file=sys.stderr)
    BeautifulSoup = None

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.page_load_strategy = 'normal'

    return options

def extract_content(driver, debug_log: List[str]) -> str:
    debug_log.append("Attempting to extract content.")
    content_elements = []
    
    for selector in ABOUT_SECTION_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                debug_log.append(f"Found elements with selector: {selector}")
                content_elements.extend(elements)
                break
        except NoSuchElementException:
            continue

    if not content_elements:
        try:
            body_element = driver.find_element(By.TAG_NAME, "body")
            content_elements = [body_element]
            debug_log.append("No specific about section found, extracting from body.")
        except NoSuchElementException:
            debug_log.append("Could not find body element.")
            return ""

    full_text = ""
    for element in content_elements:
        try:
            text = element.get_attribute('innerText')
            if text:
                full_text += text + "\n"
        except Exception as e:
            debug_log.append(f"Error getting text from element: {e}")
            
    if BeautifulSoup:
        soup = BeautifulSoup(full_text, 'html.parser')
        for selector in NAV_SELECTORS:
            for tag in soup.select(selector):
                tag.extract()

        cleaned_text = soup.get_text(separator=' ', strip=True)
        debug_log.append(f"Extracted {len(cleaned_text)} characters of content.")
        return cleaned_text
    else:
        debug_log.append("BeautifulSoup not available, returning raw text.")
        return full_text.strip()

def normalize_url(url: str, debug_log: List[str]) -> str:
    original_url = url
    debug_log.append(f"Normalizing URL: {original_url}")

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        debug_log.append(f"Added HTTPS scheme: {url}")

    parsed_url = urlparse(url)
    
    if not parsed_url.netloc:
        debug_log.append(f"Invalid URL after scheme addition (no netloc): {url}")
        return ""

    cleaned_url = urlunparse(parsed_url._replace(fragment='', query=''))
    debug_log.append(f"Cleaned URL (removed fragment/query): {cleaned_url}")
    return cleaned_url

def find_about_page_path(driver, initial_url: str, debug_log: List[str]) -> Optional[str]:
    debug_log.append(f"Searching for 'about' links on {driver.current_url}")
    
    potential_links = []
    
    try:
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            link_text = link.text.strip()
            
            if not href:
                continue

            normalized_href = normalize_url(href, debug_log)
            if not normalized_href:
                continue
            
            is_internal = urlparse(normalized_href).netloc == urlparse(initial_url).netloc

            if any(kw in normalized_href.lower() for kw in ABOUT_URL_KEYWORDS) or \
               any(pattern.search(link_text) for pattern in ABOUT_LINK_TEXT_PATTERNS):
                
                parsed_href = urlparse(normalized_href)
                path_segments = parsed_href.path.lower().split('/')
                if not any(kw in path_segments for kw in IRRELEVANT_KEYWORDS):
                    potential_links.append((normalized_href, is_internal))
                    if any(pattern.search(link_text) for pattern in ABOUT_LINK_TEXT_PATTERNS):
                        debug_log.append(f"Found strong 'about' link by text: {link_text} -> {href}")
                        return normalized_href
                    elif any(kw in normalized_href.lower() for kw in ABOUT_URL_KEYWORDS):
                         debug_log.append(f"Found strong 'about' link by URL keyword: {href}")
                         return normalized_href

    except Exception as e:
        debug_log.append(f"Error while finding about page links: {e}")
        return None

    if potential_links:
        internal_links = [link for link, is_internal in potential_links if is_internal]
        external_links = [link for link, is_internal in potential_links if not is_internal]

        if internal_links:
            debug_log.append(f"Selected internal 'about' link: {internal_links[0]}")
            return internal_links[0]
        elif external_links:
            debug_log.append(f"Selected external 'about' link (as no internal found): {external_links[0]}")
            return external_links[0]
    
    debug_log.append("No suitable 'about' link found.")
    return None

def _scrape_process(business_id: str, url: str, return_dict: dict):
    driver = None
    service = None
    scraped_content = ""
    status = "failed_unknown"
    final_url_attempted = url
    debug_log = [f"Starting scrape process for ID: {business_id}, URL: {url}"]

    chromedriver_log_path = Path(f"chromedriver_log_{business_id}.txt")

    try:
        debug_log.append("Setting up WebDriver.")
        service = ChromeService(log_path=str(chromedriver_log_path))
        driver_options = setup_driver()
        driver = webdriver.Chrome(service=service, options=driver_options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(IMPLICIT_WAIT)
        
        normalized_initial_url = normalize_url(url, debug_log)
        if not normalized_initial_url:
            status = "failed_invalid_initial_url"
            debug_log.append(f"Initial URL '{url}' normalized to an invalid format.")
            return_dict['scraped_content'] = scraped_content
            return_dict['status'] = status
            return_dict['final_url_attempted'] = final_url_attempted
            return_dict['debug_log'] = debug_log
            return_dict['business_id'] = business_id # Ensure business_id is returned even on early exit
            return

        debug_log.append(f"Navigating to initial URL: {normalized_initial_url}")
        driver.get(normalized_initial_url)
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        debug_log.append(f"Page loaded: {driver.current_url}")
        final_url_attempted = driver.current_url
        status = "success_original_url"

        initial_content = extract_content(driver, debug_log)
        if len(initial_content) >= MIN_CONTENT_LENGTH:
            scraped_content = initial_content
            status = "success_content_found"
            debug_log.append(f"Initial page has enough content ({len(initial_content)} chars).")
        else:
            debug_log.append(f"Initial page content too short ({len(initial_content)} chars). Looking for about page.")
            
            about_url = find_about_page_path(driver, normalized_initial_url, debug_log)
            if about_url and normalize_url(about_url, debug_log) != normalize_url(final_url_attempted, debug_log):
                debug_log.append(f"Attempting to navigate to found 'about' URL: {about_url}")
                try:
                    driver.get(about_url)
                    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    debug_log.append(f"Navigated to about page: {driver.current_url}")
                    final_url_attempted = driver.current_url
                    scraped_content = extract_content(driver, debug_log)
                    if len(scraped_content) >= MIN_CONTENT_LENGTH:
                        status = "success_followed_link"
                        debug_log.append(f"Successfully scraped content from followed link ({len(scraped_content)} chars).")
                    else:
                        status = "failed_content_too_short_followed"
                        debug_log.append(f"Followed link content too short ({len(scraped_content)} chars).")
                except TimeoutException:
                    status = "failed_timeout_followed_link"
                    debug_log.append(f"Timeout navigating to followed about link: {about_url}")
                except WebDriverException as e:
                    status = "failed_webdriver_followed_link"
                    debug_log.append(f"WebDriver error navigating to followed about link: {e}")
                    try:
                        debug_log.append(f"Page source on WebDriver error: {driver.page_source[:500]}...")
                    except Exception as ps_e:
                        debug_log.append(f"Could not get page source on WebDriver error: {ps_e}")
                except Exception as e:
                    status = "failed_exception_followed_link"
                    debug_log.append(f"General error navigating to followed about link: {e}")
            else:
                status = "failed_no_about_link_found"
                debug_log.append("No suitable 'about' link found or already on about page.")

    except TimeoutException:
        status = "failed_timeout_initial"
        debug_log.append(f"Timeout while loading initial URL: {url}")
    except WebDriverException as e:
        status = "failed_webdriver_error_initial"
        debug_log.append(f"WebDriver error for initial URL: {url} - {e}")
        try:
            debug_log.append(f"Page source on WebDriver error: {driver.page_source[:500]}...")
        except Exception as ps_e:
            debug_log.append(f"Could not get page source on WebDriver error: {ps_e}")
    except Exception as e:
        status = "failed_general_exception"
        debug_log.append(f"General exception during scrape for URL: {url} - {e}")
    finally:
        if driver:
            try:
                debug_log.append("Quitting driver.")
                driver.quit()
                debug_log.append("Driver quit successfully.")
            except Exception as e:
                debug_log.append(f"Error quitting driver: {e}")
        if service:
            try:
                debug_log.append("Stopping service.")
                service.stop()
                debug_log.append("Service stopped successfully.")
            except Exception as e:
                debug_log.append(f"Error stopping service: {e}")
        else:
            debug_log.append("Driver or service was not initialized, no need to quit/stop.")

    return_dict['scraped_content'] = scraped_content
    return_dict['status'] = status
    return_dict['final_url_attempted'] = final_url_attempted
    return_dict['debug_log'] = debug_log
    return_dict['business_id'] = business_id # Ensure business_id is always returned

def scrape_about_page_selenium(business_id: str, url: str) -> Dict[str, Any]:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    debug_log = [f"Attempting to scrape {url} with process timeout {PROCESS_TIMEOUT_SECONDS}s"]

    process = multiprocessing.Process(target=_scrape_process, args=(business_id, url, return_dict))
    process.start()
    process.join(timeout=PROCESS_TIMEOUT_SECONDS)

    if process.is_alive():
        process.terminate()
        process.join()
        status = "failed_process_timeout"
        debug_log.append(f"Process timed out after {PROCESS_TIMEOUT_SECONDS} seconds and was terminated.")
        scraped_content = ""
        final_url_attempted = url
    else:
        scraped_content = return_dict.get('scraped_content', "")
        status = return_dict.get('status', "failed_no_result_from_process")
        final_url_attempted = return_dict.get('final_url_attempted', url)
        debug_log.extend(return_dict.get('debug_log', []))
        
    debug_log.append(f"Scraping attempt for {url} finished with status: {status}")

    return {
        "scraped_content": scraped_content,
        "status": status,
        "final_url_attempted": final_url_attempted,
        "debug_log": debug_log,
        "business_id": business_id
    }

if __name__ == "__main__":
    test_urls = [
        "https://www.google.com/about/",
        "apswarriors.com",
        "https://www.apple.com/about/",
        "https://example.com",
        "https://www.microsoft.com/en-us/about",
        "https://www.morganstanley.com/about-us",
        "https://www.tasteofsolae.com",
        "http://www.badurlthatdoesntexist12345.com",
        "https://httpbin.org/delay/5",
        "https://httpbin.org/status/404",
        "www.albemarle.com",
        "https://www.cocacolaompany.com/about-us/our-company",
        "https://www.amazon.com/about",
        "https://www.ibm.com/about",
    ]

    test_business_ids = [f"biz_{i}" for i in range(len(test_urls))]

    for i, url in enumerate(test_urls):
        biz_id = test_business_ids[i]
        print(f"\n===== Running Scrape Test for {url} (ID: {biz_id}) =====")
        
        original_process_timeout = PROCESS_TIMEOUT_SECONDS
        PROCESS_TIMEOUT_SECONDS = 30
        
        result = scrape_about_page_selenium(biz_id, url)
        
        PROCESS_TIMEOUT_SECONDS = original_process_timeout

        print(f"\n--- Scrape Result Summary for {url} (ID: {biz_id}) ---")
        print(f"Status: {result['status']}")
        print(f"Final URL Attempted: {result['final_url_attempted']}")
        if result['scraped_content']:
            print(f"Scraped content length: {len(result['scraped_content'])} chars")
            print(f"Content Snippet: {result['scraped_content'][:200]}...")
        else:
            print("Scraped content length: 0 chars")
            print("Content Snippet: [N/A]")

        print("\n--- Full Debug Log ---")
        for log_entry in result["debug_log"]:
            print(f"    {log_entry}")
        print("--------------------------\n")
