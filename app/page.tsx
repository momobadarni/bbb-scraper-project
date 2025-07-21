// src/app/page.tsx
'use client';

import { useState, useEffect } from 'react';

interface Business {
  id: number;
  name: string;
  phone?: string;
  address?: string;
  url?: string;
  accreditation_status?: boolean;
  principal_contact?: string;
  scraped_at: string;
  source?: string;
}

export default function Home() {
  const [url, setUrl] = useState('https://www.bbb.org/search?filter_category=60548-100&filter_category=60142-000&filter_ratings=A&find_country=USA&find_text=Medical+Billing&page=1');
  const [isLoading, setIsLoading] = useState(false);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [message, setMessage] = useState('');
  const [scrapeSource, setScrapeSource] = useState<'stagehand' | 'api'>('stagehand');
  const [viewSource, setViewSource] = useState<'all' | 'stagehand' | 'api'>('all');
  const [pages, setPages] = useState(1);
  const [scrapeDuration, setScrapeDuration] = useState<number | null>(null);

  // Load existing businesses on component mount
  useEffect(() => {
    fetchBusinesses();
  }, [viewSource]);

  const fetchBusinesses = async () => {
    try {
      const response = await fetch('/api/fetch');
      const result = await response.json();
      
      if (result.success) {
        // Filter by source if needed
        let filteredData = result.data;
        if (viewSource !== 'all') {
          filteredData = result.data.filter((b: Business) => b.source === viewSource);
        }
        setBusinesses(filteredData);
      }
    } catch (error) {
      console.error('Error fetching businesses:', error);
    }
  };

  const handleScrape = async () => {
    setIsLoading(true);
    setMessage('');
    setScrapeDuration(null);
    
    const startTime = Date.now();
    
    try {
      const endpoint = scrapeSource === 'api' ? '/api/scrape-api' : '/api/scrape';
      const body = { url, pages };
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const result = await response.json();
      
      const endTime = Date.now();
      const duration = (endTime - startTime) / 1000; // Convert to seconds
      setScrapeDuration(duration);
      
      if (result.success) {
        const pagesInfo = result.pagesScraped ? ` from ${result.pagesScraped} pages` : '';
        setMessage(`Successfully scraped ${result.count} businesses${pagesInfo} in ${duration.toFixed(2)}s using ${scrapeSource.toUpperCase()}!`);
        // Refresh the list
        await fetchBusinesses();
      } else {
        setMessage(`Error: ${result.error}`);
      }
    } catch (error) {
      const endTime = Date.now();
      const duration = (endTime - startTime) / 1000;
      setScrapeDuration(duration);
      setMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredBusinesses = businesses;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">BBB Medical Billing Scraper</h1>
      
      {/* Scrape Form */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-semibold mb-4">Scrape BBB Listings</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">BBB Search URL or Search Term:</label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="Enter BBB search URL or search term"
          />
        </div>
        
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">Scrape Method:</label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="stagehand"
                  checked={scrapeSource === 'stagehand'}
                  onChange={(e) => setScrapeSource(e.target.value as 'stagehand')}
                  className="mr-2"
                />
                Stagehand (Browser)
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="api"
                  checked={scrapeSource === 'api'}
                  onChange={(e) => setScrapeSource(e.target.value as 'api')}
                  className="mr-2"
                />
                API (Fast)
              </label>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Pages to Scrape:</label>
            <input
              type="number"
              min="1"
              max="50"
              value={pages}
              onChange={(e) => setPages(parseInt(e.target.value) || 1)}
              className="w-20 p-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
        
        <button
          onClick={handleScrape}
          disabled={isLoading || !url}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md"
        >
          {isLoading ? 'Scraping...' : 'Start Scraping'}
        </button>
        
        {message && (
          <div className={`mt-4 p-2 rounded ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
          </div>
        )}
      </div>

      {/* Results Display */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">
            Scraped Businesses ({filteredBusinesses.length})
          </h2>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">View Source:</label>
            <select
              value={viewSource}
              onChange={(e) => setViewSource(e.target.value as 'all' | 'stagehand' | 'api')}
              className="p-1 border border-gray-300 rounded"
            >
              <option value="all">All Sources</option>
              <option value="stagehand">Stagehand Only</option>
              <option value="api">API Only</option>
            </select>
          </div>
        </div>
        
        {filteredBusinesses.length === 0 ? (
          <p className="text-gray-500">No businesses found. Try scraping some data!</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Phone</th>
                  <th className="px-4 py-2 text-left">Address</th>
                  <th className="px-4 py-2 text-left">Accredited</th>
                  <th className="px-4 py-2 text-left">Contact</th>
                  <th className="px-4 py-2 text-left">Source</th>
                  <th className="px-4 py-2 text-left">Scraped</th>
                </tr>
              </thead>
              <tbody>
                {filteredBusinesses.map((business) => (
                  <tr key={business.id} className="border-t">
                    <td className="px-4 py-2">
                      {business.url ? (
                        <a href={business.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          {business.name}
                        </a>
                      ) : (
                        business.name
                      )}
                    </td>
                    <td className="px-4 py-2">{business.phone || '-'}</td>
                    <td className="px-4 py-2">{business.address || '-'}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${business.accreditation_status ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {business.accreditation_status ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-4 py-2">{business.principal_contact || '-'}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        business.source === 'api' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {business.source || 'stagehand'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {new Date(business.scraped_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}