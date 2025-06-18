import asyncio
import time
from typing import List, Dict, Any
import json
# Import the scraping function from your selenium_scraper.py
# Ensure selenium_scraper.py is in the same directory or accessible via Python path
from selenium_scraper import scrape_about_page_selenium

async def run_intensive_test_suite():
    """
    Runs an intensive test suite for the selenium_scraper.py,
    focusing on problematic URLs and providing detailed debug output.
    """
    print("--- Starting Intensive Debugging Test Suite ---")

    # List of URLs to test intensively.
    # Include the problematic 'tasteofsolae.fcom' and other challenging URLs.
    test_urls = [
        "https://www.tasteofsolae.com", # The problematic URL
       
    ]

    results: List[Dict[str, Any]] = []

    for i, url in enumerate(test_urls):
        print(f"\n===== TEST {i+1}/{len(test_urls)}: Scraping {url} =====")
        start_time = time.time()

        scrape_result = {
            "url": url,
            "status": "test_suite_error",
            "final_url_attempted": None,
            "scraped_content_length": 0,
            "content_snippet": "N/A",
            "debug_log": ["Error: Test suite failed to get a result from scraper."],
            "duration_seconds": 0.0
        }

        try:
            # Call the main scraping function
            result_from_scraper = scrape_about_page_selenium(url)

            scrape_result["status"] = result_from_scraper["status"]
            scrape_result["final_url_attempted"] = result_from_scraper["final_url_attempted"]
            
            scraped_content = result_from_scraper["scraped_content"]
            if scraped_content:
                scrape_result["scraped_content_length"] = len(scraped_content)
                scrape_result["content_snippet"] = scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content
            else:
                scrape_result["scraped_content_length"] = 0
                scrape_result["content_snippet"] = "No content scraped or content not relevant."
            
            scrape_result["debug_log"] = result_from_scraper["debug_log"]

        except Exception as e:
            # Catch any unexpected errors from the scraper itself
            scrape_result["status"] = f"critical_scraper_crash: {type(e).__name__}"
            scrape_result["debug_log"].append(f"CRITICAL: Scraper crashed with exception: {e}")
            print(f"CRITICAL ERROR: Scraper crashed for {url}: {e}")
        finally:
            end_time = time.time()
            scrape_result["duration_seconds"] = round(end_time - start_time, 2)
            results.append(scrape_result)

            # Print summary for current URL
            print(f"--- Summary for {url} ---")
            print(f"  Status: {scrape_result['status']}")
            print(f"  Final URL Attempted: {scrape_result['final_url_attempted']}")
            print(f"  Scraped Content Length: {scrape_result['scraped_content_length']} chars")
            print(f"  Content Snippet: {scrape_result['content_snippet']}")
            print(f"  Duration: {scrape_result['duration_seconds']} seconds")
            print("\n--- Full Debug Log ---")
            for log_entry in scrape_result["debug_log"]:
                print(f"    {log_entry}")
            print("--------------------------\n")

    print("\n--- Intensive Debugging Test Suite Finished ---")
    print("\n--- Overall Results Summary ---")
    for res in results:
        print(f"URL: {res['url']}")
        print(f"  Status: {res['status']}")
        print(f"  Duration: {res['duration_seconds']}s")
        print(f"  Content Length: {res['scraped_content_length']}")
        print("-" * 20)

    # Optionally, save results to a JSON file for later analysis
    output_filename = "intensive_test_results.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print(f"\nDetailed test results saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(run_intensive_test_suite())