// src/app/api/scrape-api/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const fastApiUrl = process.env.FASTAPI_URL || 'http://localhost:8000'

const supabase = createClient(supabaseUrl, supabaseKey)

interface FastAPIBusiness {
  business_id: string;
  name: string;
  phone: string | null;
  principal_contact: string | null;
  url: string;
  street_address: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  accreditation_status: boolean;
}

interface FastAPIResponse {
  total_businesses: number;
  pages_scraped: number;
  businesses: FastAPIBusiness[];
}

export async function POST(request: NextRequest) {
  try {
    const { url, pages = 1 } = await request.json();
    
    // Call FastAPI scraper
    const response = await fetch(`${fastApiUrl}/scrape`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        search_input: url,
        pages: pages
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'FastAPI scraper failed');
    }

    const data: FastAPIResponse = await response.json();
    
    // Transform data for Supabase
    const businessesToInsert = data.businesses.map(business => ({
      name: business.name,
      phone: business.phone,
      address: [
        business.street_address,
        //business.city,
        //business.state,
        //business.postal_code
      ].filter(Boolean).join(', ') || null,
      url: business.url,
      accreditation_status: business.accreditation_status,
      principal_contact: business.principal_contact,
      source: 'api'
    }));

    // Businesses are already deduplicated by the FastAPI scraper using business IDs
    const uniqueBusinesses = businessesToInsert;
    
    // Save to Supabase
    const { data: savedData, error } = await supabase
      .from('businesses')
      .insert(uniqueBusinesses)
      .select();

    if (error) {
      throw error;
    }
    
    return NextResponse.json({ 
      success: true, 
      data: uniqueBusinesses,
      count: uniqueBusinesses.length,
      saved: savedData?.length || 0,
      pagesScraped: data.pages_scraped
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return NextResponse.json({ 
      success: false, 
      error: errorMessage 
    }, { status: 500 });
  }
}