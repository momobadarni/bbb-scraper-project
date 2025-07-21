import asyncio
import re
import json
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from curl_cffi.requests import AsyncSession
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants from the original script
COOKIES = {
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

HEADERS = {
    'accept': 'application/json',
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
}

# Pydantic models
class ProxyConfig(BaseModel):
    http: Optional[str] = None
    https: Optional[str] = None

class ScrapeRequest(BaseModel):
    search_input: str = Field(..., description="BBB search URL with filters or a search term")
    pages: int = Field(default=1, ge=1, le=50, description="Number of pages to scrape")
    proxy: Optional[ProxyConfig] = Field(default=None, description="Optional proxy configuration")

    @validator('search_input')
    def validate_search_input(cls, v):
        if not v.strip():
            raise ValueError("Search input cannot be empty")
        return v.strip()

class BusinessContact(BaseModel):
    prefix: Optional[str] = None
    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    full_name: Optional[str] = None

class Business(BaseModel):
    business_id: str
    name: str
    phone: Optional[str] = None
    principal_contact: Optional[str] = None
    url: str
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    accreditation_status: bool = False

class ScrapeResponse(BaseModel):
    total_businesses: int
    pages_scraped: int
    businesses: List[Business]

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="BBB Scraper API",
    description="Fast asynchronous BBB business scraper using curl_cffi",
    version="1.0.0"
)

class BBBScraper:
    def __init__(self, proxy: Optional[ProxyConfig] = None):
        self.proxy = proxy
        self.session = None
        self.retry_count = 3
        self.retry_delay = 1

    async def __aenter__(self):
        proxy_dict = None
        if self.proxy:
            proxy_dict = {}
            if self.proxy.http:
                proxy_dict['http'] = self.proxy.http
            if self.proxy.https:
                proxy_dict['https'] = self.proxy.https
        
        self.session = AsyncSession(
            cookies=COOKIES,
            headers=HEADERS,
            impersonate="chrome",
            proxies=proxy_dict
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def process_search_input(self, search_input: str, page: int = 1) -> str:
        """Process search input to generate BBB search URL"""
        # Check if it's already a BBB URL
        if 'bbb.org/search' in search_input:
            # Parse the URL and update/add page parameter
            parsed = urlparse(search_input)
            query_params = parse_qs(parsed.query)
            query_params['page'] = [str(page)]
            
            # Rebuild the URL
            new_query = urlencode(query_params, doseq=True)
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        else:
            
            base_url = "https://www.bbb.org/search"
            params = {
                'find_country': 'USA',
                'find_text': search_input,
                'page': page
            }
            return f"{base_url}?{urlencode(params)}"

    async def fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL with retry mechanism"""
        for attempt in range(self.retry_count):
            try:
                response = await self.session.get(url)
                if response.status_code == 200:
                    return response.text
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} for {url}, attempt {attempt + 1}")
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Client error {response.status_code} for {url}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching {url}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                continue
        return None

    def extract_json_data(self, html: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from HTML"""
        pattern = r'window\.__PRELOADED_STATE__\s*=\s*({.*?});</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON data")
                return None
        return None

    async def scrape_search_page(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single search results page"""
        html = await self.fetch_with_retry(url)
        if not html:
            return []

        data = self.extract_json_data(html)
        if not data or 'searchResult' not in data:
            return []

        businesses = []
        search_results = data.get('searchResult', {}).get('results', [])
        
        for result in search_results:
            business_data = {
                'businessId': result.get('businessId'),
                'businessName': result.get('businessName', '').replace('<em>', '').replace('</em>', ''),
                'phone': result.get('phone'),
                'reportUrl': result.get('reportUrl'),
                'address': result.get('address'),
                'city': result.get('city'),
                'state': result.get('state'),
                'postalcode': result.get('postalcode'),
                'accreditedCharity': result.get('accreditedCharity', False)
            }
            
            # Process phone number
            if business_data['phone']:
                phone = business_data['phone'][0] if isinstance(business_data['phone'], list) else business_data['phone']
                digits = ''.join(filter(str.isdigit, phone))
                business_data['phone'] = f"+1{digits}" if digits else None
            
            # Build full URL
            if business_data['reportUrl']:
                business_data['reportUrl'] = f"https://www.bbb.org{business_data['reportUrl']}"
            
            businesses.append(business_data)
        
        return businesses

    async def fetch_business_details(self, business_url: str) -> Optional[str]:
        """Fetch principal contact for a business"""
        html = await self.fetch_with_retry(business_url)
        if not html:
            return None

        data = self.extract_json_data(html)
        if not data or 'businessProfile' not in data:
            return None

        contacts = data.get('businessProfile', {}).get('contactInformation', {}).get('contacts', [])
        
        for contact in contacts:
            if contact.get('isPrincipal'):
                name = contact.get('name')
                if name:
                    # Only include name parts that are not None
                    name_parts = []
                    if name.get('prefix'):
                        name_parts.append(name['prefix'])
                    if name.get('first'):
                        name_parts.append(name['first'])
                    if name.get('middle'):
                        name_parts.append(name['middle'])
                    if name.get('last'):
                        name_parts.append(name['last'])
                    
                    if name_parts:
                        return ' '.join(name_parts)
        
        return None

    async def scrape(self, search_input: str, pages: int) -> ScrapeResponse:
        """Main scraping method"""
        all_businesses = []
        seen_business_ids = set()
        
        # Phase 1: Scrape all search pages concurrently
        search_tasks = []
        for page in range(1, pages + 1):
            url = self.process_search_input(search_input, page)
            search_tasks.append(self.scrape_search_page(url))
        
        logger.info(f"Scraping {pages} search pages concurrently...")
        search_results = await asyncio.gather(*search_tasks)
        
        # Flatten and deduplicate results
        for page_results in search_results:
            for business in page_results:
                business_id = business.get('businessId')
                if business_id and business_id not in seen_business_ids:
                    seen_business_ids.add(business_id)
                    all_businesses.append(business)
        
        logger.info(f"Found {len(all_businesses)} unique businesses")
        
        # Phase 2: Fetch details for all businesses concurrently
        if all_businesses:
            detail_tasks = []
            for business in all_businesses:
                if business.get('reportUrl'):
                    detail_tasks.append(self.fetch_business_details(business['reportUrl']))
                else:
                    detail_tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder
            
            logger.info(f"Fetching details for {len(all_businesses)} businesses concurrently...")
            principal_contacts = await asyncio.gather(*detail_tasks)
            
            # Update businesses with principal contacts
            for business, principal_contact in zip(all_businesses, principal_contacts):
                business['principal_contact'] = principal_contact
        
        # Convert to response model
        businesses_list = []
        for business in all_businesses:
            businesses_list.append(Business(
                business_id=business.get('businessId', ''),
                name=business.get('businessName', ''),
                phone=business.get('phone'),
                principal_contact=business.get('principal_contact'),
                url=business.get('reportUrl', ''),
                street_address=business.get('address'),
                city=business.get('city'),
                state=business.get('state'),
                postal_code=business.get('postalcode'),
                accreditation_status=business.get('accreditedCharity', False)
            ))
        
        return ScrapeResponse(
            total_businesses=len(businesses_list),
            pages_scraped=pages,
            businesses=businesses_list
        )

@app.post("/scrape", response_model=ScrapeResponse, responses={
    400: {"model": ErrorResponse, "description": "Bad request"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def scrape_bbb(request: ScrapeRequest):
    """
    Scrape BBB search results
    
    - **search_input**: Either a full BBB search URL or a search term
    - **pages**: Number of pages to scrape (1-50)
    - **proxy**: Optional proxy configuration
    """
    try:
        async with BBBScraper(proxy=request.proxy) as scraper:
            result = await scraper.scrape(request.search_input, request.pages)
            return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "BBB Scraper API"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "BBB Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "POST /scrape": "Scrape BBB search results",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)