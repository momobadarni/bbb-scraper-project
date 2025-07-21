# BBB Scraper Project + Web App

A comprehensive BBB (Better Business Bureau) scraper system with Python scrapers, Stagehand automation, and a full-stack web application.

## Project Overview

This project consists of three main parts:
- **Part A**: Python-based scrapers using Playwright and requests/curl_cffi
- **Part B**: Stagehand automation module using TypeScript/Next.js
- **Part C**: Web application with database integration using Supabase

---

## Part A: Scraper Development (BBB Medical Billing)

### Goal
Write scrapers that collect all A-rated "Medical Billing" listings from BBB and export clean CSV files.

### Search URL
https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing&page=1

### Scope
- Scrape pages 1-15 (or more) from the BBB search URL
- Extract:
  - name
  - phone (formatted as +14155551234)
  - principal_contact
  - url
  - street address
  - accreditation status
- Enforce deduplication, respectful crawling, and data accuracy

### Method Overview

#### 1. Playwright Scraper (`bbb_scraper_playwright.py`)
- Uses headed/headless browser automation
- Extracts data from page, depends on page layout not changing 
- Fast enough and reliable but tough to scale

#### 2. Requests/curl_cffi Scraper (`bbb_scraper_requests.py`)
- Direct HTTP requests using curl_cffi
- Extracts data from `window.__PRELOADED_STATE__` JSON
- Faster than browser automation
- Includes deduplication by business ID, 

#### 3. FastAPI Scraper (`bbb_fastapi_scraper.py`)
- REST API wrapper around the curl_cffi scraper
- Supports both BBB URLs and search terms
- Async concurrent scraping for multiple pages
- Built-in retry mechanism

### Reproduction Instructions

1. Install requirements:
```bash
cd Part_A_Python_Scripts
pip install -r requirements.txt
```

2. For Playwright scraper, install browser dependencies:
```bash
playwright install
```

3. Run the scrapers:
```bash
# Playwright version
python bbb_scraper_playwright.py

# Requests version  
python bbb_scraper_requests.py

# FastAPI version
python bbb_fastapi_scraper.py
# Then access http://localhost:8000/docs
```

### Issues Encountered
- BBB returns different indexed results for the same search term and page
- I had no issues using the headed mode but ran into some cloudflare blocks when trying to get headless to run Turns out playwright uses a "bot" user agent in headless mode. Forcing a specific device UA solved the headless issue. 
- As for issues while scraping, inspecting the HTML to find the needed targets was not that difficult.
- I noticed BBB retuerns different indexed results for the same search term and page, so consecutive runs of the script can still result in different total distinct business counts. 


### Deliverables
- `medical_billing_companies.csv` - Output file with scraped data

---

## Part B: Stagehand Automation Module

### Goal
Wrap the scraper into a Stagehand-compatible module for programmatic invocation using TypeScript/Next.js.

### Scope
- Stagehand script that:
  - Accepts a BBB search URL
  - Runs scraping end-to-end using AI-powered extraction
  - Returns structured JSON payload
  - Supports multi-page scraping with configurable batch sizes

### Implementation Details

#### Stagehand Script (`src/app/lib/stagehand-scraper.ts`)
- Uses BrowserBase for reliable browser automation
- AI-powered extraction using GPT-4o
- Handles both search result pages and individual business pages
- Batch processing to avoid timeouts
- Automatic deduplication by phone number

### Prompt Format

There are two prompts used, one to get all busiess URLs from the search page and pagination. 

```typescript

const urlInstruction = "Extract the URL (href attribute) for ALL business cards on this search results page. Each business card has a link to its detail page.";
```

One to extract all the other details from the business detail page. 

```typescript
// Extract detailed information from the business page
    const detailInstruction = `Extract the following information from this business detail page:
    1. Business name (usually in the header)
    2. Phone number (format as +1 followed by 10 digits)
    3. Street address only (no city, state, or zip)
    4. Principal contact name (look for "Principal Contacts" section - this is a person's name, not the phone)
    5. Accreditation status (look for "BBB Accredited Business" label or seal - return "true" or "false")`;
```

### Invocation Steps
1. Set up environment variables:
```env
BROWSERBASE_API_KEY=your_api_key
BROWSERBASE_PROJECT_ID=your_project_id
OPENAI_API_KEY=your_openai_key
```

2. Import and use the scraper:
```typescript
import { scrapeBBBPages } from '@/app/lib/stagehand-scraper';

const results = await scrapeBBBPages({
  baseUrl: "your_bbb_search_url",
  totalPages: 3
});
```

OR - Run it directly via test script

```typescript

  npx tsx run-scraper.ts --url "https://www.bbb.org/search?find_text=plumbers" --pages 3
'''
### Output Structure
```typescript
interface BusinessInfo {
  name: string;
  phone: string | null;
  address: string | null;
  url: string;
  accreditationStatus: string;
  principalContact: string | null;
}
```

### Stagehand vs Playwright Considerations
- **Stagehand**: Better for complex extraction patterns, AI-powered understanding
- **Playwright**: Better for precise, deterministic scraping of known elements

---

## Part C: Web App + Database Integration

### Goal
Build a minimal web application that ties the scraper modules into a GUI workflow with persistent storage using Supabase.

### Features

#### Front-end UI
- Simple form to submit target URLs or search terms
- Radio buttons to choose scraping method (Stagehand or API)
- Page count selector for multi-page scraping
- Real-time scraping duration display
- Filter results by source (Stagehand vs API)

#### Backend API
Multiple endpoints for different scraping methods:

1. **Stagehand Scraper** (`/api/scrape`)
   - Uses Stagehand automation
   - Slower but more reliable
   - Handles complex page structures

2. **FastAPI Scraper** (`/api/scrape-api`)
   - Uses curl_cffi for speed
   - Much faster than browser automation
   - May encounter more blocking

3. **Data Fetch** (`/api/fetch`)
   - Retrieves stored results from Supabase
   - Supports filtering by source

#### Database Schema
```sql
CREATE TABLE public.businesses (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  phone TEXT,
  address TEXT,
  url TEXT,
  accreditation_status BOOLEAN,
  principal_contact TEXT,
  source TEXT DEFAULT 'stagehand',
  scraped_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);
```

### Setup & Run

1. **Prerequisites**:
   - Node.js 18+
   - Supabase account
   - BrowserBase account
   - OpenAI API key

2. **Environment Variables**:
Create `.env.local`:
```env
# BrowserBase
BROWSERBASE_API_KEY=your_key
BROWSERBASE_PROJECT_ID=your_project_id

# OpenAI
OPENAI_API_KEY=your_openai_key

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# FastAPI URL (optional)
FASTAPI_URL=http://localhost:8000
```

3. **Install & Run**:
```bash
cd bbb-stagehand-scraper
npm install
npm run dev
```

4. **Database Setup**:
Run the schema SQL in your Supabase SQL editor

5. **Start FastAPI** (for API scraping):
```bash
cd Part_A_Python_Scripts
python bbb_fastapi_scraper.py
```

### Usage

1. Open http://localhost:3000
2. Enter a BBB search URL or search term
3. Choose scraping method (Stagehand or API)
4. Select number of pages to scrape
5. Click "Start Scraping"
6. View results in the table below
7. Filter by source to compare methods

### Tech Stack
- **Frontend**: Next.js 15.4, React, TypeScript
- **Styling**: Tailwind CSS
- **Scraping**: Stagehand + BrowserBase, curl_cffi
- **AI**: OpenAI GPT-4o
- **Database**: Supabase (PostgreSQL)
- **API**: Next.js API routes + FastAPI


### Performance Comparison
- **Stagehand**: ~30-60s per page (browser-based)
- **FastAPI**: ~2-5s per page (HTTP requests)
- Both methods include principal contact extraction

---

## Complete Project Structure

```
bbb-scraper-project/
├── Part_A_Python_Scripts/
│   ├── bbb_scraper_playwright.py
│   ├── bbb_scraper_requests.py
│   ├── bbb_fastapi_scraper.py
│   ├── requirements.txt
│   └── Output/
│       └── medical_billing_companies.csv
└── bbb-stagehand-scraper/
    ├── src/
    │   └── app/
    │       ├── api/
    │       │   ├── scrape/         # Stagehand endpoint
    │       │   ├── scrape-api/     # FastAPI endpoint
    │       │   └── fetch/          # Data retrieval
    │       ├── lib/
    │       │   └── stagehand-scraper.ts
    │       └── page.tsx           # Frontend UI
    ├── schema.sql
    └── package.json
```
