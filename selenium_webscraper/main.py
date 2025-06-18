import asyncio
import time
import json
import random
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from config import DATA_PATH, CLASSIFICATION_WEIGHTS, PROCESS_TIMEOUT_SECONDS, MIN_CONTENT_LENGTH, BATCH_SIZE, REQUEST_DELAY_SECONDS, BATCH_DELAY_SECONDS
from load_data import load_businesses, Business
from detect_poor_scrape import get_bad_scrapes, calculate_scrape_score
from selenium_scraper import scrape_about_page_selenium

GOOD_ENOUGH_SCORE_THRESHOLD = 2.0

async def run_full_pipeline():
    print("--- Starting Full Scraping Pipeline ---")
    
    all_businesses = load_businesses(DATA_PATH)
    print(f"Loaded {len(all_businesses)} businesses from {DATA_PATH.name}")

    businesses_to_rescrap = []
    business_map = {b._id: b for b in all_businesses}

    print("--- Identifying businesses for re-scraping (bad scrapes based on current classification) ---")
    count_bad_scrapes_identified = 0
    for business in all_businesses:
        if not business.web_url:
            business.selenium_status = "skipped_no_url"
            business.selenium_debug_info = ["Skipped: No web_url provided for this business."]
            business.selenium_scraped_content_length = 0 
            continue

        existing_data_for_score = {
            'combined_text': business.combined_text,
            'web_url': business.web_url,
            'raw_text': business.raw_text,
            'about_text': business.about_text
        }
        existing_score = calculate_scrape_score(existing_data_for_score)
        
        needs_rescraping = existing_score < GOOD_ENOUGH_SCORE_THRESHOLD

        if needs_rescraping:
            businesses_to_rescrap.append(business)
            count_bad_scrapes_identified += 1
        else:
            business.selenium_status = "skipped_prefilter"
            business.selenium_debug_info = ["Skipped: Existing content deemed sufficient or already successfully scraped."]
            business.selenium_scraped_content_length = getattr(business, 'selenium_scraped_content_length', len(business.combined_text) if business.combined_text else 0)


    print(f"Identified {count_bad_scrapes_identified} businesses as 'bad scrapes' for potential re-scraping.")

    print(f"Proceeding with all {len(businesses_to_rescrap)} identified bad scrapes for re-scraping.")

    total_businesses_to_process = len(businesses_to_rescrap)
    processed_count_in_pipeline = 0

    print(f"\n--- Starting Selenium Scraping in Batches (Batch Size: {BATCH_SIZE}, Per Scrape Delay: {REQUEST_DELAY_SECONDS}s, Batch Delay: {BATCH_DELAY_SECONDS}s) ---")
    start_time = time.time()

    for i in range(0, total_businesses_to_process, BATCH_SIZE):
        batch = businesses_to_rescrap[i : i + BATCH_SIZE]
        current_batch_num = i // BATCH_SIZE + 1
        total_batches = total_businesses_to_process // BATCH_SIZE + (1 if total_businesses_to_process % BATCH_SIZE else 0)
        print(f"\n--- Processing Batch {current_batch_num} of {total_batches} ---")

        for business in batch:
            processed_count_in_pipeline += 1
            print(f"\n--- Scraping Business {processed_count_in_pipeline}/{total_businesses_to_process} ---")
            print(f"Company: {business.company_name}")
            print(f"URL: {business.web_url}")

            scrape_result = {}
            try:
                scrape_result = await asyncio.to_thread(scrape_about_page_selenium, business._id, business.web_url)

                business_to_update = business_map[business._id]
                business_to_update.combined_text = scrape_result['scraped_content'] if scrape_result['scraped_content'] else business_to_update.combined_text
                business_to_update.selenium_status = scrape_result['status']
                business_to_update.selenium_scraped_content_length = len(scrape_result['scraped_content']) if scrape_result['scraped_content'] else 0
                business_to_update.selenium_debug_info = scrape_result['debug_log']

                print(f"Status: {business_to_update.selenium_status}")
                if business_to_update.combined_text:
                    print(f"Scraped Text (first 500 chars): {business_to_update.combined_text[:500]}...")
                else:
                    print(f"Scraped Text: None")

            except Exception as e:
                print(f"ERROR during scrape for {business.company_name} ({business.web_url}): {e}")
                business_to_update = business_map[business._id]
                business_to_update.selenium_status = f"error_main_pipeline: {e}"
                business_to_update.selenium_debug_info = getattr(business_to_update, 'selenium_debug_info', [])
                business_to_update.selenium_debug_info.append(f"Main pipeline error: {e}")
                business_to_update.selenium_scraped_content_length = 0
            finally:
                await asyncio.sleep(REQUEST_DELAY_SECONDS)
        
        if i + BATCH_SIZE < total_businesses_to_process:
            print(f"\n--- Batch {current_batch_num} completed. Waiting {BATCH_DELAY_SECONDS} seconds before next batch ---")
            await asyncio.sleep(BATCH_DELAY_SECONDS)


    end_time = time.time()
    print(f"\nSelenium scraping of identified bad scrapes completed in {end_time - start_time:.2f} seconds.")

    processed_businesses_output = []
    for business in all_businesses:
        biz_output_dict = {
            '_id': business._id,
            'seq_num': business.seq_num,
            'duns_num': business.duns_num,
            'duns_status': business.duns_status,
            'company_name': business.company_name,
            'tradestyle': business.tradestyle,
            'top_contact': business.top_contact,
            'title': business.title,
            'street_address': business.street_address,
            'phone': business.phone,
            'web_url': business.web_url,
            'total_emps': business.total_emps,
            'emps_on_site': business.emps_on_site,
            'sales_volume': business.sales_volume,
            'public_private': business.public_private,
            'year_started': business.year_started,
            'latitude': business.latitude,
            'longtitude': business.longtitude,
            'naics_1_num': business.naics_1_num,
            'naics_1_title': business.naics_1_title,
            'naics_2_num': business.naics_2_num,
            'naics_2_title': business.naics_2_title,
            'sic_1_num': business.sic_1_num,
            'sic_1_title': business.sic_1_title,
            'sic_2_num': business.sic_2_num,
            'sic_2_title': business.sic_2_title,
            'number_of_locations': business.number_of_locations,
            'date_of_report': business.date_of_report,
            'raw_text': business.raw_text,
            'about_text': business.about_text,
            'combined_text': business.combined_text,
            'raw_token_count': business.raw_token_count,
            'about_token_count': business.about_token_count,
            'combined_token_count': getattr(business, 'combined_token_count', None),

            'selenium_scraped_data': business.combined_text,
            'selenium_status': getattr(business, 'selenium_status', 'not_processed'),
            'selenium_scraped_content_length': getattr(business, 'selenium_scraped_content_length', 0),
            'selenium_debug_info': getattr(business, 'selenium_debug_info', [])
        }
        processed_businesses_output.append(biz_output_dict)

    print("\n--- Classifying Scrapes ---")
    classified_businesses = []
    for biz_data in processed_businesses_output:
        original_score = calculate_scrape_score(biz_data)

        selenium_data_for_score = {
            'combined_text': biz_data.get('combined_text'),
            'web_url': biz_data.get('web_url')
        }
        selenium_score = calculate_scrape_score(selenium_data_for_score)

        is_good_scrape = (biz_data.get('selenium_status') in ["success_content_found", "success_original_url", "success_direct_path", "success_followed_link"]) and \
                         (biz_data.get('selenium_scraped_content_length', 0) > MIN_CONTENT_LENGTH) and \
                         (selenium_score >= GOOD_ENOUGH_SCORE_THRESHOLD)

        classified_businesses.append({
            '_id': biz_data['_id'],
            'company_name': biz_data['company_name'],
            'web_url': biz_data['web_url'],
            'original_combined_text_snippet': (biz_data.get('raw_text') or biz_data.get('about_text') or '')[:200] + '...' if (biz_data.get('raw_text') or biz_data.get('about_text')) else '[N/A]',
            'selenium_scraped_content_snippet': biz_data.get('combined_text', '')[:200] + '...' if biz_data.get('combined_text') else '[N/A]',
            'selenium_status': biz_data.get('selenium_status'),
            'selenium_scraped_content_length': biz_data.get('selenium_scraped_content_length'),
            'original_score': original_score,
            'selenium_score': selenium_score,
            'final_is_good_scrape': is_good_scrape,
            'selenium_debug_info': biz_data.get('selenium_debug_info')
        })

    final_good_scrapes_info = []
    final_bad_scrapes_info = []

    for entry in classified_businesses:
        if entry['final_is_good_scrape']:
            final_good_scrapes_info.append(entry)
        else:
            final_bad_scrapes_info.append(entry)

    print(f"\nFinal Good Scrapes: {len(final_good_scrapes_info)}")
    print(f"Final Bad Scrapes: {len(final_bad_scrapes_info)}")
    
    print("\n--- Sample of Final Good Scrapes ---")
    for b in final_good_scrapes_info[:5]:
        print(f"ID: {b['_id']}, Name: {b['company_name']}, Status: {b['selenium_status']}, Scraped Length: {b['selenium_scraped_content_length']}, Good: {b['final_is_good_scrape']}")

    print("\n--- Sample of Final Bad Scrapes ---")
    for b in final_bad_scrapes_info[:5]:
        print(f"ID: {b['_id']}, Name: {b['company_name']}, Status: {b['selenium_status']}, Scraped Length: {b['selenium_scraped_content_length']}, Good: {b['final_is_good_scrape']}")
        if b['selenium_debug_info']:
            print(f"  Selenium Debug Info (last entry): {b['selenium_debug_info'][-1]}")

    output_file = Path("full_business_scrape_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_businesses_output, f, indent=4)
    print(f"\nFull business scrape results saved to {output_file.name}")


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())