import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";


export async function scrapeBBBPage(url: string) {
  const stagehand = new Stagehand({
    env: "BROWSERBASE",
    apiKey: process.env.BROWSERBASE_API_KEY,
    projectId: process.env.BROWSERBASE_PROJECT_ID || "",
    browserbaseSessionCreateParams: {
      projectId: process.env.BROWSERBASE_PROJECT_ID || "",
      browserSettings: {
        // Set viewport
        viewport: {
          width: 1024,
          height: 768,
        },
        // Basic fingerprint settings
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
      // Add IPRoyal proxy configuration
     /* proxies: [{
        type: "external",
        server: "http://geo.iproyal.com:12321",
        username: "OSnJGwxgZKM4t6CG",
        password: "kHc8njV9L8PjMyfn_country-us_session-9HuePVps_lifetime-59m_streaming-1"
      }]*/
     proxies: true
    },
    modelName: "openai/gpt-4o-mini",
    modelClientOptions: {
      apiKey: process.env.OPENAI_API_KEY,
    },
    verbose: 1
  });
  
  await stagehand.init();
  
  const page = stagehand.page;
  
  // Navigate to target site
  await page.goto(url);
  
  // Wait for content to load
  await page.waitForLoadState('networkidle');
  
  const instruction = "Extract the information for ALL the businesses cards on the page, name, phone (formatted as +14155551234), street address (no city, no state), link to the business detail page, accreditation status (this is not the rating, but the accreditation status based on the BBB seal - return true or false), principal contact ( this is not the phone number, but name of the contact, if its not there then let it be null)";
  /*const instruction = `
const instruction = `
Extract information for ALL business cards visible on this BBB search results page.

For each business card, extract:

1. NAME: The full business name as displayed in the card header

2. PHONE: Extract and format as +1 followed by 10 digits (example: +14155551234)
   - Remove all spaces, dashes, parentheses, and dots
3. ADDRESS: Street address ONLY (no city, state, or zip)
  
4. URL: The FULL BBB.org URL for the business detail page - href attribute

5. ACCREDITATION STATUS: Boolean true/false
   - Look for "BBB Accredited Business" text or BBB seal/badge
   - true = has "Accredited Business" label or BBB seal
   - false = no accreditation indicator

6. PRINCIPAL CONTACT: The contact person's name if shown
   - This is a person's name, NOT the phone number
   - If not visible, return null
`;*/

  const result = await page.extract({
    instruction: instruction,
    schema: z.object({
      list_of_businesses: z.array(z.object({
        name: z.string(),
        phone: z.string(),
        address: z.string(),
        url: z.string().url(),
        accreditationStatus: z.string(),
        principalContact: z.string().nullable(),
      }))
    }),
  });
  
  await stagehand.close();
  
  return result.list_of_businesses;
}

