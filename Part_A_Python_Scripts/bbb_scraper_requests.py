import time
import re
import csv
import re
import json
from curl_cffi import requests

cookies = {
    'iabbb_user_culture': 'en-us',
    'iabbb_user_location': 'Ellicott_MD_USA',
    'iabbb_user_physical_location': 'Ellicott%20City%2C%20MD%2C%20US',
    'iabbb_user_bbb': '0011',
    'iabbb_find_location': 'Ellicott_MD_USA',
    'iabbb_session_id': '03226eee-01af-4dc8-abba-57e0da8874e7',
    'iabbb_cookies_policy': '%7B%22necessary%22%3Atrue%2C%22functional%22%3Afalse%2C%22performance%22%3Afalse%2C%22marketing%22%3Afalse%7D',
    'iabbb_cookies_preferences_set': 'true',
    'iabbb_accredited_toggle_state': 'seen',
    'iabbb_user_postalcode': '21043',
    '__cf_bm': 'Q1QJt7U.s429_lUvLHoVXYjvoUz1wWfJfJoEB78gIkI-1752980338-1.0.1.1-ud8uWgCUOHRbFDVxIabmMFMJeLBHQO57m_enOirxdCNrHl2PrtuiWNP3VE_0YoS1FrF0VwOyIiSQEUG5t9xKgADXtmSI4kzlsDR36ewxEdI',
    'CF_Authorization': 'eyJraWQiOiIxY2VlNzA1OGQ0NjE1MDBhOTE1Y2U3Yjk2MWE3ZGRhMTAzMWRiYmJhMmUxYjc1YzBkMzI4MjBiOTYwNmQxNTJiIiwiYWxnIjoiUlMyNTYiLCJ0eXAiOiJKV1QifQ.eyJ0eXBlIjoiYXBwIiwiYXVkIjoiMmNhYzEyYTJmOWY0OTI2YjdmYmY3OTJmNTA5MjA1NjA5YWMwMmIwZmQ0MWQ1ZTcyZjY0YzY5NWY3MDg2ODkzYyIsImV4cCI6MTc1MzA2NjczOCwiaXNzIjoiaHR0cHM6XC9cL2lhYmJiLmNsb3VkZmxhcmVhY2Nlc3MuY29tIiwiY29tbW9uX25hbWUiOiJhNTBlNTEzYjFjNzM0ZjFhMjJmZDJlN2ZkMjI5ZmI4NC5hY2Nlc3MiLCJpYXQiOjE3NTI5ODAzMzgsInN1YiI6IiJ9.1dvkN7SQllrXbkfT6fQvCP4wVXw6v0kOTh2RVO83-h401tokctEqWD-IALm7DMNhydLje0pkpUTvru3c83xw5MjvP9yEhW9GLdpKUrds_V3Q_NAFoaKHCFTERQjwluJES5R6NAURIULqkcqqMPJh7cyqbb4CsDaxrPSkkMX76WWOef0xD4XZUqXmRagNcf-M82-Qp5dAhVM6OrgW9if-FXfva5u9GhrL2eM2VpkMETrULYlWz16_oza50UCA2Jf_Pi3k3r2BEyZoS6DAtKfUOvq_wfBpY5RmNMbUGIUidFQiW8zJEIIw9cJX03PZZKOrD7QpDW18sEqzhVx3l0ElgQ',
    '__gads': 'ID=f09ab7c25269b925:T=1752881631:RT=1752980338:S=ALNI_MafSVlTpcJSLepszPtNxBqrj74log',
    '__eoi': 'ID=74c03c9a04af405d:T=1752881631:RT=1752980338:S=AA-AfjZs-NMi6Oo6MILmCP8fh4ch',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept':'application/json',
    'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    # 'cookie': 'iabbb_user_culture=en-us; iabbb_user_location=Ellicott_MD_USA; iabbb_user_physical_location=Ellicott%20City%2C%20MD%2C%20US; iabbb_user_bbb=0011; iabbb_find_location=Ellicott_MD_USA; iabbb_session_id=03226eee-01af-4dc8-abba-57e0da8874e7; iabbb_cookies_policy=%7B%22necessary%22%3Atrue%2C%22functional%22%3Afalse%2C%22performance%22%3Afalse%2C%22marketing%22%3Afalse%7D; iabbb_cookies_preferences_set=true; iabbb_accredited_toggle_state=seen; iabbb_user_postalcode=21043; __cf_bm=Q1QJt7U.s429_lUvLHoVXYjvoUz1wWfJfJoEB78gIkI-1752980338-1.0.1.1-ud8uWgCUOHRbFDVxIabmMFMJeLBHQO57m_enOirxdCNrHl2PrtuiWNP3VE_0YoS1FrF0VwOyIiSQEUG5t9xKgADXtmSI4kzlsDR36ewxEdI; CF_Authorization=eyJraWQiOiIxY2VlNzA1OGQ0NjE1MDBhOTE1Y2U3Yjk2MWE3ZGRhMTAzMWRiYmJhMmUxYjc1YzBkMzI4MjBiOTYwNmQxNTJiIiwiYWxnIjoiUlMyNTYiLCJ0eXAiOiJKV1QifQ.eyJ0eXBlIjoiYXBwIiwiYXVkIjoiMmNhYzEyYTJmOWY0OTI2YjdmYmY3OTJmNTA5MjA1NjA5YWMwMmIwZmQ0MWQ1ZTcyZjY0YzY5NWY3MDg2ODkzYyIsImV4cCI6MTc1MzA2NjczOCwiaXNzIjoiaHR0cHM6XC9cL2lhYmJiLmNsb3VkZmxhcmVhY2Nlc3MuY29tIiwiY29tbW9uX25hbWUiOiJhNTBlNTEzYjFjNzM0ZjFhMjJmZDJlN2ZkMjI5ZmI4NC5hY2Nlc3MiLCJpYXQiOjE3NTI5ODAzMzgsInN1YiI6IiJ9.1dvkN7SQllrXbkfT6fQvCP4wVXw6v0kOTh2RVO83-h401tokctEqWD-IALm7DMNhydLje0pkpUTvru3c83xw5MjvP9yEhW9GLdpKUrds_V3Q_NAFoaKHCFTERQjwluJES5R6NAURIULqkcqqMPJh7cyqbb4CsDaxrPSkkMX76WWOef0xD4XZUqXmRagNcf-M82-Qp5dAhVM6OrgW9if-FXfva5u9GhrL2eM2VpkMETrULYlWz16_oza50UCA2Jf_Pi3k3r2BEyZoS6DAtKfUOvq_wfBpY5RmNMbUGIUidFQiW8zJEIIw9cJX03PZZKOrD7QpDW18sEqzhVx3l0ElgQ; __gads=ID=f09ab7c25269b925:T=1752881631:RT=1752980338:S=ALNI_MafSVlTpcJSLepszPtNxBqrj74log; __eoi=ID=74c03c9a04af405d:T=1752881631:RT=1752980338:S=AA-AfjZs-NMi6Oo6MILmCP8fh4ch',
}

def scrape_bbb_results():
    businesses = []
    seen_businesses = set()
    for i in range(1,16):
        print(f"Scraping page {i}")
        url = f"https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing&page={i}"
        response = requests.get(url, headers=headers,impersonate="chrome")
        print(response.status_code)
        # Extract the JSON data using regex
        pattern = r'window\.__PRELOADED_STATE__\s*=\s*({.*?});</script>'
        match = re.search(pattern, response.text, re.DOTALL)
        
        if match:
            # Parse the JSON
            data = json.loads(match.group(1))
            
            # Extract results
            search_results = data['searchResult']['results']
            
           
            
            # Process each result
            for result in search_results:
                businessId = result['businessId']
                if businessId in seen_businesses:
                    continue
                seen_businesses.add(businessId)
                name = result['businessName']
                name = name.replace('<em>', '').replace('</em>', '')
                if result['phone'] is not None:
                    phone = result['phone'][0] # Extract the first phone number if there are multiple
                    digits = ''.join(filter(str.isdigit, phone))
                    phone = f"+1{digits}"
                else:
                    phone = None
                accreditedCharity = result['accreditedCharity']
                url = result['reportUrl']
                url = f"https://www.bbb.org{url}"
                street_address = result['address']
                #accreditation_status = result['accreditationStatus']
                #rating = result['rating']
                print(f"Business: {name}")
                print(f"Address: {street_address}, {result['city']}, {result['state']} {result['postalcode']}")
                print(f"Phone: {phone}")
                print(f"URL: {url}")
                print(f"Accredited Charity: {accreditedCharity}") # this is the accreditation status
                print(f"Business ID: {businessId}")
                #print(f"Rating: {rating}")
                print("-" * 50)

                businesses.append({
                    'name': name,
                    'phone': phone,
                    'principal_contact': None,
                    'url': url,
                    'street_address': street_address,
                    'accreditation_status': accreditedCharity
                })

    for business in businesses:
        url = business['url']
        response = requests.get(url, headers=headers,impersonate="chrome")
        #print(response.status_code)
        # Extract the JSON data using regex
        pattern = r'window\.__PRELOADED_STATE__\s*=\s*({.*?});</script>'
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            # Parse the JSON
            data = json.loads(match.group(1))
            contacts = data['businessProfile']['contactInformation']['contacts']
            for contact in contacts:
                if contact['isPrincipal'] == True:
                    if contact['name'] is not None:
                        name = contact['name']
                        contact_name = f"{name.get('prefix', '')} {name.get('first', '')} {name.get('middle', '')} {name.get('last', '')}"
                        contact_name = contact_name.strip()
                        business['principal_contact'] = contact_name
                        break
        else:
            print("No match found")
    print(f"Found {len(businesses)} distinct businesses")
    save_to_csv(businesses)

           
        
    

    
def save_to_csv(businesses):
    """Save businesses to CSV file"""
    if not businesses:
        print("No businesses to save")
        return
    
    fieldnames = ['name', 'phone', 'principal_contact', 'url', 'street_address', 'accreditation_status']
    
    with open('Part_A_Python_Scripts/Output/medical_billing_companies_v2.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)
    
    print(f"Saved {len(businesses)} businesses to medical_billing_companies_v2.csv")


if __name__ == '__main__':
    scrape_bbb_results()