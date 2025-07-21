import asyncio
from playwright.async_api import async_playwright
import time
import re
import csv
import traceback

def extract_business_id_from_url(url):
    """Extract business ID from BBB URL"""
    if not url:
        return None
    # Pattern to match business ID (series of digits after the last hyphen before optional /addressId)
    pattern = r'-(\d+)(?:/addressId/\d+)?/?$'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

async def extract_business_info(card):
        """Extract business info from a single card based on the actual BBB structure"""
        try:
            # Business name - from h3.result-business-name a
            name_element = await card.query_selector('h3.result-business-name a')
            name = None
            if name_element:
                name = await name_element.inner_text()
               
            
            # Phone number - from a[href^="tel:"]
            phone_element = await card.query_selector('a[href^="tel:"]')
            phone = None
            if phone_element:
                # Get the actual displayed phone number
                phone = await phone_element.inner_text()
                digits = ''.join(filter(str.isdigit, phone))
                phone = f"+1{digits}"
            
            # Business URL - from h3.result-business-name a href
            url = None
            business_id = None
            if name_element:
                url = await name_element.get_attribute('href')
                if url:
                    url = 'https://www.bbb.org' + url
                    business_id = extract_business_id_from_url(url)
            
            # Address - from the address paragraph
            address_element = await card.query_selector('.result-business-info p[translate="no"]')
            street_address = None
            if address_element:
                address_text = await address_element.inner_text()
                # Extract just the street address (before the comma or line break)
                if address_text:
                    # Remove line breaks and clean up
                    address_text = address_text.replace('\n', ' ').strip()
                    # Try to extract just the street address part
                    street_address = address_text.split(',')[0].strip() if ',' in address_text else address_text
            
            # Accreditation status - check for BBB seal image
            accredited_element = await card.query_selector('img[alt="Accredited Business"]')
            accreditation_status = accredited_element is not None
            
            
            
            
            return {
                'business_id': business_id,
                'name': name.strip(),
                'phone': phone,
                'principal_contact': None, 
                'url': url,
                'street_address': street_address,
                'accreditation_status': accreditation_status,
            }
        
        except Exception as e:
            print(f"Error extracting business info: {e}")
            print(traceback.format_exc())
        
        return None



async def scrape_bbb_playwright(base_url=None, num_pages=15):
    """
    Scrape BBB search results
    
    Args:
        base_url: The BBB search URL (defaults to medical billing search)
        num_pages: Number of pages to scrape (default 15)
    """
    if not base_url:
        base_url = 'https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing'
    
    # Import URL parsing utilities
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    async with async_playwright() as p:
        businesses = []
        firefox = p.devices['Desktop Firefox'] #needed this to get headless working

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
                **firefox,)
        
        page = await context.new_page()
        # Create a second page for fetching principal contacts
        detail_page = await context.new_page()
        
        # Parse the base URL to handle page parameter
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Phase 1: Collect all businesses from search pages
        all_businesses = []
        for pageNumber in range(1, num_pages + 1):
            # Build URL with page parameter
            query_params['page'] = [str(pageNumber)]
            new_query = urlencode(query_params, doseq=True)
            page_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            
            print(f"\nScraping page {pageNumber} of {num_pages}...")
            await page.goto(page_url)
        
            # Wait for results to load
            await page.wait_for_selector('.card.result-card')
            
            business_cards = await page.query_selector_all('.card.result-card')
            print(f"Found {len(business_cards)} business cards")
            
            # Extract all business data from the search results page
            for i, card in enumerate(business_cards):
                print(f"Processing business {i+1}...")
                business_data = await extract_business_info(card)
                if business_data:
                    all_businesses.append(business_data)
                    print(f"  - {business_data.get('name', 'Unknown')}")
        
        print(f"\nTotal businesses collected from search: {len(all_businesses)}")
        
        # Phase 2: Deduplicate businesses before fetching details
        unique_businesses = {}
        for business in all_businesses:
            if business.get('business_id'):
                unique_businesses[business['business_id']] = business
            elif business.get('phone'):  # Fallback to phone if no business ID
                unique_businesses[business['phone']] = business
        
        deduplicated_businesses = list(unique_businesses.values())
        print(f"Unique businesses after deduplication: {len(deduplicated_businesses)}")
        
        # Phase 3: Fetch principal contacts for deduplicated businesses
        print(f"\nFetching principal contacts for {len(deduplicated_businesses)} businesses...")
        for idx, business_data in enumerate(deduplicated_businesses):
            if business_data and business_data['url']:
                try:
                    print(f"Fetching details {idx+1}/{len(deduplicated_businesses)}: {business_data.get('name', 'Unknown')}")
                    await detail_page.goto(business_data['url'])
                    await detail_page.wait_for_load_state('networkidle')
                    
                    principal_contact = await detail_page.query_selector('dt:has-text("Principal Contacts") + dd')
                    if principal_contact:
                        contact_text = await principal_contact.inner_text()
                        # Remove role/position (everything after comma) but keep titles
                        if ',' in contact_text:
                            contact_text = contact_text.split(',')[0].strip()
                        business_data['principal_contact'] = contact_text
                    else:
                        business_data['principal_contact'] = None
                except Exception as e:
                    print(f"Error fetching principal contact: {e}")
                    business_data['principal_contact'] = None
        
        businesses = deduplicated_businesses

        print(f"\nTotal distinct businesses extracted: {len(businesses)}")
        # Save to CSV
        save_to_csv(businesses)
        
        await browser.close()
        return businesses

    
def save_to_csv(businesses):
    """Save businesses to CSV file"""
    
    
    fieldnames = ['name', 'phone', 'principal_contact', 'url', 'street_address', 'accreditation_status']
    
    with open('Output/medical_billing_companies.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        # Write businesses without business_id field
        for business in businesses:
            row = {k: v for k, v in business.items() if k != 'business_id'}
            writer.writerow(row)
    
    print(f"Saved {len(businesses)} businesses to medical_billing_companies.csv")


if __name__ == '__main__':
    
    url = "https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing"
    pages = 15
    asyncio.run(scrape_bbb_playwright(url, pages))