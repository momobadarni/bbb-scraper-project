// src/app/api/businesses/route.ts
import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

const supabase = createClient(supabaseUrl, supabaseKey)
export async function GET() {
  try {
    const { data, error } = await supabase
      .from('businesses')
      .select('*')
      .order('scraped_at', { ascending: false });

    if (error) {
      throw error;
    }

    return NextResponse.json({ 
      success: true, 
      data: data || [],
      count: data?.length || 0
    });
  } catch (error) {
    return NextResponse.json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }, { status: 500 });
  }
}