import { runScraper } from "./stagehand-scraper";
import * as fs from 'fs';
import * as path from 'path';



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
  main();