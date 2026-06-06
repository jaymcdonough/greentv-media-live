# GreenTV Square Online Site Build Guide (greentvapp.square.site)

## Current State of https://greentvapp.square.site/
It is using Square's default "eCommerce template for appointments". It is not blank - it has placeholder content:
- "greentv" header
- "Book Appointment" buttons everywhere
- Fake San Francisco location (1274 Alhambra Court, San Francisco, CA 94107)
- Hours Mon-Fri 9-5, Sat 9-5, Sun closed
- Newsletter signup
- Payment icons (Cash App, Apple Pay, Google Pay, cards)
- "Powered by Square"

This is typical for a new/unedited Square Online site.

## Why You Don't See the Items in Dashboard
All our previous work (catalog population, customers) was done using the **sandbox** token and environment.

The greentvapp.square.site and the Square Dashboard you are looking at are **production**.

Sandbox items only exist in the test environment. They don't show in your main dashboard or on the live site.

## How to Fix It (Production Population)

1. **Get your production keys**
   - Go to https://developer.squareup.com/apps (log in with the account that owns greentvapp.square.site)
   - Find your production application (not the sandbox one)
   - Go to Credentials
   - Copy:
     - Production Application ID
     - Production Access Token (the full long EAAA... token for production)

2. **Update the keys file**
   Edit `/c/Users/Green/OneDrive/Desktop/square_api_info.txt` and add the production section (I already added placeholders).

3. **Update square_config.py**
   In square_config.py, set:
   - "application_id" to your prod app ID
   - "access_token" to the full prod token
   - "environment": "production"
   - Keep or update "location_id" (run the script to discover if needed)

4. **Re-run the population for production**
   cd to the square-integration folder
   python populate_catalog.py

5. **Verify in your Square Dashboard**
   - Log into https://squareup.com/dashboard (the production one)
   - Go to Items > Catalog
   - You should now see the 4 GreenTV items:
     - GreenTV Share - $1,000
     - GreenTV Pro Membership - $49/mo
     - GreenTV Studio Membership - $149/mo
     - Custom GreenTV Investment (for negotiated deals)

6. **Enable for Online Store**
   In the dashboard, make sure the items are available for your Online Store / the greentvapp site.

## How to Build Out the Actual greentvapp.square.site

Square Online sites are edited in the visual editor (not via API for full content).

Log into Square Dashboard > Online > Sites > greentvapp (or the site name) > Edit site.

### Recommended Content to Paste (from the approved prototype)

**Hero Section**
Headline: TRUTH. SOLUTIONS. ACTION.
Subheadline: Independent media powered by AI. Real stories. Real impact. Real revenue for creators and partners.
Primary button: "Choose Your Path - Get Started"
Secondary: "Submit Your Story for Olivia Green"

**The 4 Paths (use a 4-column or grid of cards/blocks)**

1. **Activist / Freelance Journalist / Seasoned Journalist**
   "Submit your story, film, blog post or content. We turn it into a professional news segment featuring Olivia Green, our AI news anchor. Low friction. High reach. Real participation."
   Button: "Submit Content (Free - Leads to Olivia Interview)"

2. **Investor**
   "Shares at $1,000 each. Or tell us your amount and expectations for a custom product. Fuels independent truth-telling and automation that helps creators generate revenue."
   Button: "Invest $1,000/Share or Custom (Square Checkout)"

3. **Normal User / Want My Own Custom Channel**
   "Start with a free custom GreenTV channel. Upgrade to Pro or Studio memberships. Hook your accounts and sites to our powerful automation system - it can generate real money for you."
   Button: "Claim Free Channel or Subscribe"

4. **TV Show Owner / Sponsor / Partner**
   "Negotiate custom deals, sponsorships, or full automation setups. We accommodate almost anything. Benefits to you and the world explained. Amounts over $1,000 routed for approval."
   Button: "Start a Negotiation"

**Featured Products Section**
Add the 4 catalog items as products. Square Online will handle the checkout using Square's secure payment flow.

**The Olivia Green Highlight (make this prominent)**
"The biggest thing we want to promote: Submit content with title, write-up, image/video, category, links. It gets inserted into the blog engine and video pipeline. You get an email invitation to a live broadcast interview with Olivia Green.
This encourages participation with little oversight or investment and is essential to us being green."

Button: "Submit Your Movie, Blog or Story Now"

**Automation Power Callout**
"greentv.app offers the same powerful automation we use. Hook it to your accounts and sites. It can generate money when connected properly. We negotiate custom setups for serious partners."

## Additional Tips for Square Online Editor
- Replace the default "Book Appointment" with our CTAs.
- Use the product blocks for the catalog items (they will link to Square checkout automatically).
- Add custom HTML/JS blocks if allowed for the smart classifier (or link to the prototype HTML we have locally).
- Update location/hours to real GreenTV info or remove if not physical.
- Add images from the prototype or your assets.
- For the intake form that classifies user type and routes to specific CTAs: You can embed a form tool or use the self-contained prototype as a separate hosted page and link to it.

## Reference Files on Your Desktop
- greentv-square-site.html : Full self-contained reference of what the built-out site should look like (open it to see the design).
- greentv-media-onboarding-prototype.html : The smart intake with user classification and direct action CTAs. Use this as the "Get Started" destination.
- square-integration/ folder : Backend for custom payments if you want more than the built-in Square Online checkout.

## If You Update the Production Token
Paste the new production token into the txt file or tell me, and I will:
- Update the config
- Re-run the population script against production
- Confirm the items exist via API
- Send another note to VPS Hermes

This will get the real greentvapp.square.site populated with our content and the payment gateway fully hooked via Square for the investor, membership, and custom deal CTAs.

Let me know the production keys or any errors when you try the steps above.
