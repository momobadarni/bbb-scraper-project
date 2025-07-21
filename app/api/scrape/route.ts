// src/app/api/scrape/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { scrapeBBBPages } from '../../lib/stagehand-scraper';
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

const supabase = createClient(supabaseUrl, supabaseKey)

export async function POST(request: NextRequest) {
  try {
    const { url, pages = 1 } = await request.json();
    
    // Log environment for debugging
    console.log('NODE_ENV:', process.env.NODE_ENV);
    console.log('Environment variables set:', {
      BROWSERBASE_API_KEY: !!process.env.BROWSERBASE_API_KEY,
      BROWSERBASE_PROJECT_ID: !!process.env.BROWSERBASE_PROJECT_ID,
      OPENAI_API_KEY: !!process.env.OPENAI_API_KEY
    });
    
    // Scrape the businesses using the new scraper
    const scrapedBusinesses = await scrapeBBBPages({
      baseUrl: url,
      totalPages: pages
    });
    
    // Businesses are already deduplicated by the scraper using business IDs
    const uniqueBusinesses = scrapedBusinesses;
    
    // Save to Supabase
    const { data, error } = await supabase
      .from('businesses')
      .insert(uniqueBusinesses.map(business => ({
        name: business.name,
        phone: business.phone || null,
        address: business.address || null,
        url: business.url || null,
        accreditation_status: business.accreditationStatus,
        principal_contact: business.principalContact,
        source: 'stagehand'
      })))
      .select();

    if (error) {
      throw error;
    }
    
    return NextResponse.json({ 
      success: true, 
      data: uniqueBusinesses,
      count: uniqueBusinesses.length,
      saved: data?.length || 0,
      pagesScraped: pages
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return NextResponse.json({ 
      success: false, 
      error: errorMessage 
    }, { status: 500 });
  }
}