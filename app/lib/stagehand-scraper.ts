import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";

function extractBusinessIdFromUrl(url: string): string | null {
  if (!url) return null;
  // Pattern to match business ID (series of digits after the last hyphen before optional /addressId)
  const pattern = /-(\d+)(?:\/addressId\/\d+)?\/?$/;
  const match = url.match(pattern);
  if (match) {
    return match[1];
  }
  return null;
}

interface BusinessInfo {
  businessId: string | null;
  name: string;
  phone: string | null;
  address: string | null;
  url: string;
  accreditationStatus: string;
  principalContact: string | null;
}

interface ScraperConfig {
  baseUrl: string;
  totalPages: number;
  businessesPerSession?: number; // Number of businesses to process per session
}

async function createStagehandInstance() {
  // Check for required environment variables
  if (!process.env.BROWSERBASE_API_KEY || !process.env.BROWSERBASE_PROJECT_ID || !process.env.OPENAI_API_KEY) {
    throw new Error('Missing required environment variables: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, or OPENAI_API_KEY');
  }

  const isProduction = process.env.NODE_ENV === 'production';
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stagehandConfig: any = {
    env: "BROWSERBASE",
    apiKey: process.env.BROWSERBASE_API_KEY,
    projectId: process.env.BROWSERBASE_PROJECT_ID,
    browserbaseSessionCreateParams: {
      projectId: process.env.BROWSERBASE_PROJECT_ID,
      browserSettings: {
        viewport: {
          width: 1024,
          height: 768,
        },
        fingerprint: {
          browsers: ["chrome"],
          devices: ["desktop"],
          operatingSystems: ["windows"],
          locales: ["en-US"],
          httpVersion: "2",
          screen: {
            maxHeight: 1080,
            maxWidth: 1920,
            minHeight: 768,
            minWidth: 1024
          }
        },
        blockAds: true
      },
      proxies: true
    },
    modelName: "gpt-4o",
    modelClientOptions: {
      apiKey: process.env.OPENAI_API_KEY,
    },
    // Only add verbose in development to completely avoid pino-pretty in production
    verbose: isProduction ? 0 : 1
  };
  
  const stagehand = new Stagehand(stagehandConfig);
  
  await stagehand.init();
  return stagehand;
}

async function extractBusinessDetailsFromPage(stagehand: Stagehand, businessUrl: string): Promise<BusinessInfo | null> {
  try {
    const page = stagehand.page;
    
    console.log(`  Navigating to business page: ${businessUrl}`);
    await page.goto(businessUrl, { timeout: 30000 });
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Extract detailed information from the business page
    const detailInstruction = `Extract the following information from this business detail page:
    1. Business name (usually in the header)
    2. Phone number (format as +1 followed by 10 digits)
    3. Street address only (no city, state, or zip)
    4. Principal contact name (look for "Principal Contacts" section - include the person's full name with titles like Mr., Ms., Mrs., Dr., etc. but EXCLUDE any role/position that comes after a comma like Owner, President, CEO, etc.)
    5. Accreditation status (look for "BBB Accredited Business" label or seal - return "true" or "false")`;
    
    const detailResult = await page.extract({
      instruction: detailInstruction,
      schema: z.object({
        name: z.string(),
        phone: z.string().nullable(),
        address: z.string().nullable(),
        principalContact: z.string().nullable(),
        accreditationStatus: z.string(),
      }),
    });
    
    const businessId = extractBusinessIdFromUrl(businessUrl);
    
    return {
      businessId,
      ...detailResult,
      url: businessUrl,
    };
  } catch (error) {
    console.error(`  Error extracting details from ${businessUrl}:`, error);
    return null;
  }
}

async function processBusinessBatch(businesses: { url: string }[]): Promise<BusinessInfo[]> {
  const results: BusinessInfo[] = [];
  let stagehand: Stagehand | null = null;
  
  try {
    stagehand = await createStagehandInstance();
    
    for (let i = 0; i < businesses.length; i++) {
      const business = businesses[i];
      console.log(`  Processing business ${i + 1} of ${businesses.length}...`);
      
      const businessInfo = await extractBusinessDetailsFromPage(stagehand, business.url);
      
      if (businessInfo) {
        results.push(businessInfo);
        console.log(`    ✅ Added: ${businessInfo.name} (ID: ${businessInfo.businessId || 'no-id'})`);
      }
      
      // Small delay between requests to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch (error) {
    console.error('Error processing business batch:', error);
  } finally {
    if (stagehand) {
      try {
        await stagehand.close();
      } catch (closeError) {
        console.error('Error closing stagehand session:', closeError);
      }
    }
  }
  
  return results;
}

export async function scrapeBBBPages(config: ScraperConfig) {
  const { baseUrl, totalPages, businessesPerSession = 15 } = config;
  const allBusinesses: BusinessInfo[] = [];
  const seenBusinessIds = new Set<string>();
  const allBusinessUrls: { url: string }[] = [];
  
  // First, collect all business URLs from search pages
  console.log(`🔍 Collecting business URLs from ${totalPages} pages...`);
  
  let searchStagehand: Stagehand | null = null;
  try {
    searchStagehand = await createStagehandInstance();
    const page = searchStagehand.page;
    
    for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
      console.log(`\n📄 Processing search page ${pageNum} of ${totalPages}...`);
      
      // Parse the base URL and add page parameter
      const url = new URL(baseUrl);
      url.searchParams.set('page', pageNum.toString());
      const searchUrl = url.toString();
      
      try {
        // Navigate to search results page
        await page.goto(searchUrl, { timeout: 30000 });
        await page.waitForLoadState('networkidle', { timeout: 30000 });
        
        // Extract business URLs from search results
        const urlInstruction = "Extract the URL (href attribute) for ALL business cards on this search results page. Each business card has a link to its detail page.";
        
        const urlResult = await page.extract({
          instruction: urlInstruction,
          schema: z.object({
            list_of_businesses: z.array(z.object({
              url: z.string().url(),
            }))
          }),
        });
        
        console.log(`  Found ${urlResult.list_of_businesses.length} businesses on page ${pageNum}`);
        allBusinessUrls.push(...urlResult.list_of_businesses);
        
      } catch (error) {
        console.error(`Error processing search page ${pageNum}:`, error);
      }
    }
  } finally {
    if (searchStagehand) {
      try {
        await searchStagehand.close();
      } catch (closeError) {
        console.error('Error closing search session:', closeError);
      }
    }
  }
  
  console.log(`\n📊 Total business URLs collected: ${allBusinessUrls.length}`);
  
  // Deduplicate URLs by business ID before processing
  const uniqueBusinessUrls: { url: string }[] = [];
  const seenBusinessIds = new Set<string>();
  
  for (const business of allBusinessUrls) {
    const businessId = extractBusinessIdFromUrl(business.url);
    if (businessId && !seenBusinessIds.has(businessId)) {
      seenBusinessIds.add(businessId);
      uniqueBusinessUrls.push(business);
    } else if (!businessId) {
      // Keep URLs without business IDs (shouldn't happen, but just in case)
      uniqueBusinessUrls.push(business);
    }
  }
  
  console.log(`\n📊 Unique businesses after deduplication: ${uniqueBusinessUrls.length}`);
  
  // Process businesses in batches with new sessions
  console.log(`\n🚀 Processing businesses in batches of ${businessesPerSession}...`);
  
  for (let i = 0; i < uniqueBusinessUrls.length; i += businessesPerSession) {
    const batch = uniqueBusinessUrls.slice(i, i + businessesPerSession);
    console.log(`\n📦 Processing batch ${Math.floor(i / businessesPerSession) + 1} (${batch.length} businesses)...`);
    
    const batchResults = await processBusinessBatch(batch);
    allBusinesses.push(...batchResults);
    
    
  }
  
  console.log(`\n✅ Total businesses collected: ${allBusinesses.length}`);
  
  return allBusinesses;
}

// Usage with configurable parameters
export async function runScraper(baseUrl?: string, totalPages?: number) {
  const config: ScraperConfig = {
    baseUrl: baseUrl || "https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing",
    totalPages: totalPages || 3,
    businessesPerSession: 15 // Process 30 businesses per session to avoid timeouts
  };
  
  console.log(`🚀 Starting BBB scraper for ${config.totalPages} pages...`);
  console.log(`🔗 Base URL: ${config.baseUrl}`);
  
  const results = await scrapeBBBPages(config);
  console.log("\n📊 Final results:", results);
  return results;
}

/*
async function main() {
  try {
    console.log('Starting BBB scraper test...');
    
    // Get command line arguments
    const args = process.argv.slice(2);
    let baseUrl: string | undefined;
    let totalPages: number | undefined;
    
    // Parse command line arguments
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--url' && args[i + 1]) {
        baseUrl = args[i + 1];
        i++;
      } else if (args[i] === '--pages' && args[i + 1]) {
        totalPages = parseInt(args[i + 1]);
        i++;
      }
    }
    
    // Run the scraper with optional parameters
    const results = await runScraper(baseUrl, totalPages);
    
    // Save results to JSON file
    const outputDir = path.join(process.cwd(), 'output');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const outputPath = path.join(outputDir, `bbb-scrape-results-${new Date().toISOString().split('T')[0]}.json`);
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    
    console.log(`\n💾 Results saved to: ${outputPath}`);
    console.log(`📊 Total businesses scraped: ${results.length}`);
    
    // Also save as CSV
    if (results.length > 0) {
      const csvPath = path.join(outputDir, `bbb-scrape-results-${new Date().toISOString().split('T')[0]}.csv`);
      const csvHeader = 'Name,Phone,Address,URL,Accreditation Status,Principal Contact\n';
      const csvContent = results.map(b => 
        `"${b.name}","${b.phone || ''}","${b.address || ''}","${b.url}","${b.accreditationStatus}","${b.principalContact || ''}"`
      ).join('\n');
      
      fs.writeFileSync(csvPath, csvHeader + csvContent);
      console.log(`📄 CSV saved to: ${csvPath}`);
    }
    
  } catch (error) {
    console.error('Error running scraper:', error);
    process.exit(1);
  }
}

// Run the test
main();*/