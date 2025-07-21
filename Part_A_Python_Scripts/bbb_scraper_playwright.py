import asyncio
from playwright.async_api import async_playwright
import time
import re
import csv
import traceback

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
            if name_element:
                url = await name_element.get_attribute('href')
                if url:
                    url = 'https://www.bbb.org' + url
            
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



async def scrape_bbb_playwright():
    async with async_playwright() as p:
        businesses = []
        firefox = p.devices['Desktop Firefox'] #needed this to get headless working

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
                **firefox,)
        
        page = await context.new_page()
        # Create a second page for fetching principal contacts
        detail_page = await context.new_page()
        
        for pageNumber in range(1, 16):
            await page.goto(f'https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing&page={pageNumber}')
        
            # Wait for results to load
            await page.wait_for_selector('.card.result-card')
            
            business_cards = await page.query_selector_all('.card.result-card')
            print(f"Found {len(business_cards)} business cards")
            
            # First, extract all business data from the search results page
            page_businesses = []
            for i, card in enumerate(business_cards):
                print(f"Processing business {i+1}...")
                business_data = await extract_business_info(card)
                if business_data:
                    page_businesses.append(business_data)
                    print(f"  - {business_data.get('name', 'Unknown')}")
            
            # Then, fetch principal contacts using the detail page
            for business_data in page_businesses:
                if business_data and business_data['url']:
                    try:
                        await detail_page.goto(business_data['url'])
                        await detail_page.wait_for_load_state('networkidle')
                        
                        principal_contact = await detail_page.query_selector('dt:has-text("Principal Contacts") + dd')
                        if principal_contact:
                            business_data['principal_contact'] = await principal_contact.inner_text()
                        else:
                            business_data['principal_contact'] = None
                    except Exception as e:
                        print(f"Error fetching principal contact for {business_data.get('name', 'Unknown')}: {e}")
                        business_data['principal_contact'] = None
                    
                    businesses.append(business_data)

        print(f"\nTotal businesses extracted: {len(businesses)}")

        # Remove duplicates based on phone number - this methodolgy could change based on the preffered method of deduplication
        businesses = list({d['phone']: d for d in businesses}.values())
        businesses = list({d['name']: d for d in businesses}.values())
    
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
        writer.writerows(businesses)
    
    print(f"Saved {len(businesses)} businesses to medical_billing_companies.csv")


if __name__ == '__main__':
    asyncio.run(scrape_bbb_playwright())