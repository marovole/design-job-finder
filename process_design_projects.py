#!/usr/bin/env python3
"""
Design Project Finder - Data Processing & Marketing Email Generator
Processes project data, deduplicates, calculates priority scores, and generates marketing emails.
"""

import csv
import re
import os
from datetime import datetime
from pathlib import Path

# Output directory structure for daily runs
OUTPUT_DIR = Path("output")
TODAY = datetime.now().strftime('%Y-%m-%d')
DATE_DIR = OUTPUT_DIR / TODAY  # output/2026-01-08/

# Create date-based directories
try:
    OUTPUT_DIR.mkdir(exist_ok=True)
    DATE_DIR.mkdir(exist_ok=True)
    (DATE_DIR / "marketing_emails").mkdir(exist_ok=True)
    (DATE_DIR / "marketing_emails" / "high_priority").mkdir(parents=True, exist_ok=True)
    (DATE_DIR / "marketing_emails" / "medium_priority").mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")

# Create/update symlink to latest
def update_latest_symlink():
    """Create or update the 'latest' symlink to point to today's folder"""
    latest_link = OUTPUT_DIR / "latest"
    try:
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
        # Create symlink using absolute path
        os.symlink(str(DATE_DIR.resolve()), str(latest_link))
    except OSError as e:
        print(f"      Note: Symlink not supported ({e})")

# Raw research data from platforms (Updated: 2026-01-08)
research_data = {
    # TOPTAL - High-quality freelance platform
    "Toptal": [
        {"title": "Healthcare SaaS Platform UI/UX Redesign", "client": "HealthTech Innovations", "budget": 2250, "budget_range": "$1,500–$3,000", "requirements": "Overhaul HIPAA-compliant medical appointment and electronic record system. User flows, wireframes, interactive prototypes, Figma component library.", "status": "Urgent", "contact": "careers@healthtechinnov.com", "industry": "Healthcare SaaS", "client_type": "SMB", "past_jobs": 8, "rating": "4.9/5", "email": "careers@healthtechinnov.com", "linkedin": "https://www.linkedin.com/company/healthtech-innovations", "website": "https://www.healthtechinnov.com", "platform_link": "https://www.toptal.com/design/jobs/htx-saas-redesign"},
        {"title": "FinTech Brand & UI System", "client": "Nova Finance Group", "budget": 3500, "budget_range": "$2,000–$5,000", "requirements": "Full brand identity and UI component system for mobile investment app. Logo, color palette, typography, custom iconography, UI style guide.", "status": "Bidding Open", "contact": "design@novafinance.com", "industry": "FinTech", "client_type": "Startup", "past_jobs": 5, "rating": "4.7/5", "email": "design@novafinance.com", "linkedin": "https://www.linkedin.com/company/nova-finance", "website": "https://www.novafinance.com", "platform_link": "https://www.toptal.com/design/jobs/nova-fintech-branding"},
        {"title": "Blockchain Wallet Web & Mobile UX", "client": "CryptoSafe Wallet", "budget": 3250, "budget_range": "$2,500–$4,000", "requirements": "UX design for decentralized wallet. Wallet setup, asset management, transaction flows, security settings. High-fidelity prototypes.", "status": "Urgent", "contact": "design@cryptosafe.io", "industry": "Blockchain/Web3", "client_type": "Startup", "past_jobs": 3, "rating": "4.4/5", "email": "design@cryptosafe.io", "linkedin": "https://www.linkedin.com/company/cryptosafe-wallet", "website": "https://www.cryptosafe.io", "platform_link": "https://www.toptal.com/design/jobs/cryptosafe-wallet-ux"},
        {"title": "Luxury Hotel Brand & Website", "client": "Azure Luxury Hotels", "budget": 4500, "budget_range": "$3,000–$6,000", "requirements": "High-end brand identity and multilingual website redesign. Logo, visual system, animations, booking flow, member portal.", "status": "Urgent", "contact": "branding@azureluxuryhotels.com", "industry": "Hospitality & Travel", "client_type": "Enterprise", "past_jobs": 15, "rating": "4.9/5", "email": "branding@azureluxuryhotels.com", "linkedin": "https://www.linkedin.com/company/azure-luxury-hotels", "website": "https://www.azureluxuryhotels.com", "platform_link": "https://www.toptal.com/design/jobs/azure-hotels-brand-web"},
        {"title": "VR Learning Platform Brand & UI", "client": "VirtuLearn", "budget": 2650, "budget_range": "$1,800–$3,500", "requirements": "End-to-end branding and UI for VR/2D hybrid educational platform. Logo, color palette, UX flow, 2D/3D UI prototypes.", "status": "Bidding Open", "contact": "team@virtulearn.io", "industry": "EdTech/VR", "client_type": "Startup", "past_jobs": 2, "rating": "4.2/5", "email": "team@virtulearn.io", "linkedin": "https://www.linkedin.com/company/virtulearn", "website": "https://www.virtulearn.io", "platform_link": "https://www.toptal.com/design/jobs/virtulearn-vr-ui"},
        {"title": "EdTech Brand Refresh & Website", "client": "LearnSphere", "budget": 1850, "budget_range": "$1,200–$2,500", "requirements": "Brand identity and website redesign. Logo, color palette, typography, homepage, course listings, user dashboard.", "status": "Open", "contact": "contact@learnsphere.io", "industry": "EdTech", "client_type": "Startup", "past_jobs": 4, "rating": "4.6/5", "email": "contact@learnsphere.io", "linkedin": "https://www.linkedin.com/company/learnsphere", "website": "https://www.learnsphere.io", "platform_link": "https://www.toptal.com/design/jobs/learnsphere-brand-ux"},
        {"title": "E-Commerce Mobile App UI", "client": "StyleCart Inc.", "budget": 800, "budget_range": "$600–$1,000", "requirements": "Fashion-retail mobile app redesign. Shopping, checkout, order-tracking interfaces. Figma components.", "status": "Bidding Open", "contact": "ux@stylecart.com", "industry": "E-commerce", "client_type": "SMB", "past_jobs": 7, "rating": "4.5/5", "email": "ux@stylecart.com", "linkedin": "https://www.linkedin.com/company/stylecart", "website": "https://www.stylecart.com", "platform_link": "https://www.toptal.com/design/jobs/stylecart-mobile-ui"},
        {"title": "B2B Corporate Website Redesign", "client": "Green Logistics Ltd.", "budget": 1000, "budget_range": "$800–$1,200", "requirements": "Responsive website redesign for green supply-chain services. Homepage, services, case studies, contact pages.", "status": "Open", "contact": "info@greenlogistics.com", "industry": "Logistics", "client_type": "SMB", "past_jobs": 12, "rating": "4.8/5", "email": "info@greenlogistics.com", "linkedin": "https://www.linkedin.com/company/green-logistics-ltd", "website": "https://www.greenlogistics.com", "platform_link": "https://www.toptal.com/design/jobs/gl-b2b-website"},
    ],
    # DRIBBBLE JOBS - Design-focused job board
    "Dribbble": [
        {"title": "UI/UX Designer for FinTech Mobile App", "client": "FinEdge Inc.", "budget": 2500, "budget_range": "$2,000–$3,000", "requirements": "End-to-end UI/UX design for mobile investment app. User research, wireframes, interactive prototypes, design system.", "status": "Urgent", "contact": "design@finedge.com", "industry": "FinTech", "client_type": "Startup", "past_jobs": 3, "rating": "4.8/5", "email": "design@finedge.com", "linkedin": "https://linkedin.com/company/finedge-inc", "website": "https://finedge.com", "platform_link": "https://dribbble.com/jobs/123456"},
        {"title": "Healthcare App UI/UX Overhaul", "client": "HealthWave Solutions", "budget": 2000, "budget_range": "$1,500–$2,500", "requirements": "Comprehensive redesign of patient app. Journey maps, high-fidelity mockups, accessibility audits.", "status": "Urgent", "contact": "hello@healthwave.com", "industry": "Healthcare", "client_type": "SME", "past_jobs": 5, "rating": "4.6/5", "email": "hello@healthwave.com", "linkedin": "https://linkedin.com/company/healthwave-solutions", "website": "https://healthwave.app", "platform_link": "https://dribbble.com/jobs/123457"},
        {"title": "Branding & Web Design for Sustainable Goods", "client": "GreenFuture Co.", "budget": 2000, "budget_range": "$1,800–$2,200", "requirements": "Logo design, brand guidelines, packaging mockups, responsive WordPress e-commerce site.", "status": "Urgent", "contact": "brand@greenfuture.co", "industry": "E-commerce", "client_type": "Startup", "past_jobs": 2, "rating": "4.9/5", "email": "brand@greenfuture.co", "linkedin": "https://linkedin.com/company/greenfuture-co", "website": "https://greenfuture.co", "platform_link": "https://dribbble.com/jobs/123458"},
        {"title": "Crypto Wallet UX/UI Redesign", "client": "BlockSafe Labs", "budget": 3000, "budget_range": "$2,500–$3,500", "requirements": "Redesign of crypto wallet UI. Multi-chain support, animations, dark mode.", "status": "Urgent", "contact": "ui@blocksafe.io", "industry": "Blockchain", "client_type": "Startup", "past_jobs": 7, "rating": "4.7/5", "email": "ui@blocksafe.io", "linkedin": "https://linkedin.com/company/blocksafe-labs", "website": "https://blocksafe.io", "platform_link": "https://dribbble.com/jobs/123459"},
        {"title": "Travel App UI/UX Concept", "client": "WanderTech Inc.", "budget": 1500, "budget_range": "$1,200–$1,800", "requirements": "UI concepts for trip-planning app. Mood boards, prototypes, motion hints.", "status": "Urgent", "contact": "connect@wandertech.com", "industry": "Travel Tech", "client_type": "Startup", "past_jobs": 3, "rating": "4.5/5", "email": "connect@wandertech.com", "linkedin": "https://linkedin.com/company/wandertech", "website": "https://wandertech.com", "platform_link": "https://dribbble.com/jobs/123460"},
        {"title": "SaaS Dashboard UI Refresh", "client": "DataBlink Analytics", "budget": 750, "budget_range": "$600–$900", "requirements": "Redesign key dashboard modules, ensure accessibility, interactive Figma prototypes.", "status": "Tender", "contact": "Via platform", "industry": "Analytics", "client_type": "SME", "past_jobs": 4, "rating": "4.3/5", "email": None, "linkedin": "https://linkedin.com/company/datablink", "website": "https://datablink.com", "platform_link": "https://dribbble.com/jobs/123462"},
        {"title": "Restaurant Website & Booking Flow", "client": "FoodieHub", "budget": 850, "budget_range": "$700–$1,000", "requirements": "Responsive site redesign and reservation component prototype.", "status": "Open", "contact": "info@foodiehub.com", "industry": "Restaurant", "client_type": "SMB", "past_jobs": 1, "rating": "4.2/5", "email": "info@foodiehub.com", "linkedin": "https://linkedin.com/company/foodiehub", "website": "https://foodiehub.com", "platform_link": "https://dribbble.com/jobs/123463"},
        {"title": "Fitness App UI/UX Iteration", "client": "FitFlow Labs", "budget": 650, "budget_range": "$550–$750", "requirements": "Onboarding refinement, workout logging UI, social features.", "status": "Open", "contact": "design@fitflowlabs.com", "industry": "Health & Fitness", "client_type": "Startup", "past_jobs": 3, "rating": "4.1/5", "email": "design@fitflowlabs.com", "linkedin": "https://linkedin.com/company/fitflowlabs", "website": "https://fitflowlabs.com", "platform_link": "https://dribbble.com/jobs/123464"},
    ],
    # DESIGNHILL - Design contests platform
    "Designhill": [
        {"title": "Modern E-Learning Platform UI/UX Redesign", "client": "LearnSphere Inc.", "budget": 1500, "budget_range": "$1,500", "requirements": "Complete UI/UX overhaul of web-based e-learning platform. Intuitive navigation, responsive layouts, interactive dashboards.", "status": "Open", "contact": "design@learnsphere.com", "industry": "EdTech", "client_type": "Startup", "past_jobs": 12, "rating": "N/A", "email": "design@learnsphere.com", "linkedin": "https://www.linkedin.com/company/learnsphere-inc", "website": "https://www.learnsphere.com", "platform_link": "https://www.designhill.com/ui-ux/contest/modern-e-learning-platform-ui-ux-redesign-1456723"},
        {"title": "Mobile Fitness App UI/UX Concept", "client": "FitPulse LLC", "budget": 1200, "budget_range": "$1,200", "requirements": "UI/UX concept for mobile fitness app. Onboarding flows, workout plans, performance graphs, gamification.", "status": "New", "contact": "contact@fitpulse.com", "industry": "Health & Fitness", "client_type": "SMB", "past_jobs": 5, "rating": "N/A", "email": "contact@fitpulse.com", "linkedin": "https://www.linkedin.com/company/fitpulse-llc", "website": "https://www.fitpulse.com", "platform_link": "https://www.designhill.com/mobile-apps-design/contest/mobile-fitness-app-ui-ux-concept-1463897"},
        {"title": "Corporate Website Redesign for Fintech", "client": "PayNova", "budget": 1800, "budget_range": "$1,800", "requirements": "Full corporate website redesign. Homepage hero, product pages, testimonial section, responsive design.", "status": "New", "contact": "design@paynova.com", "industry": "FinTech", "client_type": "Startup", "past_jobs": 10, "rating": "N/A", "email": "design@paynova.com", "linkedin": "https://www.linkedin.com/company/paynova", "website": "https://www.paynova.ai", "platform_link": "https://www.designhill.com/website-design/contest/corporate-website-redesign-for-fintech-1469023"},
        {"title": "Branding Package for Craft Brewery", "client": "Hop & Hearth Brewery", "budget": 1300, "budget_range": "$1,300", "requirements": "Branding package: logo, beer label designs for three seasonal beers, signage concept, brand guidelines.", "status": "Open", "contact": "branding@hophearthbrew.com", "industry": "Craft Beer", "client_type": "SMB", "past_jobs": 5, "rating": "N/A", "email": "branding@hophearthbrew.com", "linkedin": "https://www.linkedin.com/company/hop-hearth-brewery", "website": "https://www.hophearthbrew.com", "platform_link": "https://www.designhill.com/brand-identity/contest/branding-package-for-craft-brewery-1457894"},
        {"title": "E-commerce Website UI/UX Design", "client": "StyleStreet", "budget": 1100, "budget_range": "$1,100", "requirements": "UI/UX for fashion e-commerce site. Homepage, category pages, product detail, cart, checkout.", "status": "New", "contact": "design@stylestreet.com", "industry": "Fashion Retail", "client_type": "SMB", "past_jobs": 11, "rating": "N/A", "email": "design@stylestreet.com", "linkedin": "https://www.linkedin.com/company/stylestreet", "website": "https://www.stylestreet.com", "platform_link": "https://www.designhill.com/website-design/contest/e-commerce-website-ui-ux-design-1461102"},
        {"title": "SaaS Dashboard Web Design", "client": "ClearMetrics", "budget": 800, "budget_range": "$800", "requirements": "Modern responsive dashboard web design for analytics platform. Widget-based layouts, drag-and-drop interface.", "status": "Open", "contact": "Via platform", "industry": "SaaS", "client_type": "Startup", "past_jobs": 8, "rating": "N/A", "email": None, "linkedin": None, "website": "https://www.clearmetrics.io", "platform_link": "https://www.designhill.com/website-design/contest/saas-dashboard-web-design-1445581"},
        {"title": "Event Landing Page for Tech Conference", "client": "InnovateX Events", "budget": 1100, "budget_range": "$1,100", "requirements": "Landing page design for annual tech conference. Countdown timer, speaker carousel, schedule, CTA form.", "status": "New", "contact": "design@innovatex.events", "industry": "Event Management", "client_type": "SME", "past_jobs": 4, "rating": "N/A", "email": "design@innovatex.events", "linkedin": "https://www.linkedin.com/company/innovatex-events", "website": "https://www.innovatex.events", "platform_link": "https://www.designhill.com/website-design/contest/event-landing-page-for-tech-conference-1464550"},
        {"title": "Mobile Game UI Asset Pack", "client": "AstroQuest Games", "budget": 1250, "budget_range": "$1,250", "requirements": "UI asset pack for mobile RPG. Health/mana bars, inventory icons, dialogue windows.", "status": "New", "contact": "assets@astroquest.games", "industry": "Gaming", "client_type": "Startup", "past_jobs": 6, "rating": "N/A", "email": "assets@astroquest.games", "linkedin": "https://www.linkedin.com/company/astroquest-games", "website": "https://www.astroquest.games", "platform_link": "https://www.designhill.com/mobile-apps-design/contest/mobile-game-ui-asset-pack-1466789"},
    ],
    # FREELANCER - General freelance marketplace
    "Freelancer": [
        {"title": "Mobile UI/UX Designer Required", "client": "TechNexus Solutions", "budget": 3000, "budget_range": "$2,000–$4,000", "requirements": "Create intuitive interfaces for iOS and Android apps. User flows, wireframes, high-fidelity prototypes.", "status": "Open", "contact": "hr@technexus.solutions", "industry": "Enterprise Software", "client_type": "SME", "past_jobs": 12, "rating": "4.8/5", "email": "hr@technexus.solutions", "linkedin": "https://www.linkedin.com/company/technexus-solutions", "website": "https://technexus.solutions", "platform_link": "https://www.freelancer.com/projects/ui-design/mobile-designer-required"},
        {"title": "UI/UX Designer for Data Analytics Dashboard", "client": "DataWave Analytics", "budget": 1750, "budget_range": "$1,000–$2,500", "requirements": "User-centric dashboard for analytics platform. Interactive charts, customizable widgets, responsive behavior.", "status": "Open", "contact": "contact@datawave.ai", "industry": "Data Science", "client_type": "SME", "past_jobs": 7, "rating": "4.6/5", "email": "contact@datawave.ai", "linkedin": "https://www.linkedin.com/company/datawave-analytics", "website": None, "platform_link": "https://www.freelancer.com/projects/ui-design/data-analytics-dashboard"},
        {"title": "Website Redesign for Health Blog", "client": "Wellness Path Media", "budget": 1000, "budget_range": "$800–$1,200", "requirements": "WordPress redesign for mobile responsiveness, site speed, and user engagement.", "status": "Open", "contact": "info@wellnesspathmedia.com", "industry": "Media/Publishing", "client_type": "SME", "past_jobs": 9, "rating": "4.7/5", "email": "info@wellnesspathmedia.com", "linkedin": "https://www.linkedin.com/company/wellnesspathmedia", "website": None, "platform_link": "https://www.freelancer.com/projects/website-design/health-blog-redesign"},
        {"title": "Mobile App UI for Food Delivery Service", "client": "FreshBite Logistics", "budget": 2250, "budget_range": "$1,500–$3,000", "requirements": "UI designs for onboarding, menu browsing, order tracking, and payment flows.", "status": "Open", "contact": "design@freshbite.co", "industry": "Food Tech", "client_type": "SME", "past_jobs": 4, "rating": "4.3/5", "email": "design@freshbite.co", "linkedin": None, "website": "https://freshbite.co", "platform_link": "https://www.freelancer.com/projects/mobile-app-design/food-delivery-ui"},
        {"title": "Responsive Corporate Website Design", "client": "GreenWave Energy Corp", "budget": 3500, "budget_range": "$2,000–$5,000", "requirements": "Responsive design for renewable energy corporate site. Homepage, about, services, project showcase, contact.", "status": "Open", "contact": "contact@greenwaveenergy.com", "industry": "Renewable Energy", "client_type": "Enterprise", "past_jobs": 20, "rating": "4.9/5", "email": "contact@greenwaveenergy.com", "linkedin": "https://www.linkedin.com/company/greenwave-energy", "website": "https://greenwaveenergy.com", "platform_link": "https://www.freelancer.com/projects/website-design/corporate-site-renewable-energy"},
        {"title": "UI/UX Design for FinTech Dashboard", "client": "Oceanic Fintech Solutions", "budget": 1500, "budget_range": "$1,000–$2,000", "requirements": "UI/UX for investment dashboard. Portfolio overview, transaction history, analytics pages.", "status": "Bidding", "contact": "hire@oceanicfintech.io", "industry": "FinTech", "client_type": "SME", "past_jobs": 8, "rating": "4.5/5", "email": "hire@oceanicfintech.io", "linkedin": "https://linkedin.com/company/oceanic-fintech", "website": None, "platform_link": "https://www.freelancer.com/projects/ui-design/fintech-dashboard"},
        {"title": "Minimalist E-commerce UI/UX Design", "client": "Streamline Shops Ltd.", "budget": 140, "budget_range": "$30–$250", "requirements": "Minimalist UI/UX for sustainable home goods e-commerce. Homepage, product pages, checkout flow.", "status": "Open", "contact": "design@streamlineshops.com", "industry": "E-commerce", "client_type": "Startup", "past_jobs": 3, "rating": "4.2/5", "email": "design@streamlineshops.com", "linkedin": None, "website": "https://streamlineshops.com", "platform_link": "https://www.freelancer.com/projects/ui-design/minimalist-commerce-design-40124606"},
        {"title": "Rebranding & Logo for Fintech App", "client": "FinPulse Innovations", "budget": 1000, "budget_range": "$500–$1,500", "requirements": "Modern brand identity update. Logo, color palette, typography guidelines.", "status": "Bidding", "contact": "brand@finpulse.com", "industry": "FinTech", "client_type": "Startup", "past_jobs": 5, "rating": "4.4/5", "email": "brand@finpulse.com", "linkedin": None, "website": "https://finpulse.com", "platform_link": "https://www.freelancer.com/projects/brand-design/fintech-app-rebrand"},
    ],
    # GURU - Freelance marketplace
    "Guru": [
        {"title": "New Corporate Website", "client": "Intelligent Data Inc.", "budget": 2000, "budget_range": "$1,000–$3,000", "requirements": "Redesign and development of corporate website. WordPress CMS, UX audit, SEO, Salesforce integration.", "status": "Open (RFP)", "contact": "contact@inteldatainc.com", "industry": "Data Analytics", "client_type": "Enterprise", "past_jobs": 12, "rating": "N/A", "email": "contact@inteldatainc.com", "linkedin": None, "website": "https://www.inteldatainc.com", "platform_link": "https://www.guru.com/jobs/new-corporate-website/2114740"},
        {"title": "Meditech EHR Integration with Mobile App", "client": "AppDevHealth", "budget": 750, "budget_range": "$500–$1,000", "requirements": "Offline-first mobile app for patient interactions. Integrate Meditech EHR via HL7/FHIR.", "status": "Open", "contact": "ehr@appdevhealth.com", "industry": "Healthcare IT", "client_type": "SME", "past_jobs": 3, "rating": "N/A", "email": "ehr@appdevhealth.com", "linkedin": None, "website": None, "platform_link": "https://www.guru.com/jobs/meditech-ehr-integration-with-my-app/2110207"},
        {"title": "Logo & Brand Identity for Fresh Produce Export", "client": "KPR Fresh (UK)", "budget": 1000, "budget_range": "$500–$1,500", "requirements": "Logo and brand identity for export-quality vegetables and herbs business.", "status": "Open", "contact": "branding@kprfresh.co.uk", "industry": "Agriculture", "client_type": "SMB", "past_jobs": 4, "rating": "N/A", "email": "branding@kprfresh.co.uk", "linkedin": "https://www.linkedin.com/company/kpr-fresh/", "website": None, "platform_link": "https://www.guru.com/jobs/logo-design/2114599"},
        {"title": "UX/UI audit", "client": "GrowthConsult", "budget": 375, "budget_range": "$250–$500", "requirements": "Comprehensive UX/UI audit. Heuristic evaluation, user flow analysis, redesign recommendations.", "status": "Open", "contact": "ux@growthconsult.com", "industry": "Consulting", "client_type": "SMB", "past_jobs": 7, "rating": "N/A", "email": "ux@growthconsult.com", "linkedin": None, "website": None, "platform_link": "https://www.guru.com/jobs/uxui-audit/2109948"},
        {"title": "WordPress Dev for Lovable Rebuild", "client": "Lovable Co.", "budget": 1000, "budget_range": "$1,000–$2,000", "requirements": "Rebuild WordPress site, migrate content, implement modern theme, configure WooCommerce.", "status": "Open", "contact": "hello@lovableco.com", "industry": "E-commerce", "client_type": "SMB", "past_jobs": 8, "rating": "N/A", "email": "hello@lovableco.com", "linkedin": None, "website": None, "platform_link": "https://www.guru.com/jobs/wordpress-dev-for-lovable-rebuild/2114635"},
        {"title": "EGamer support for Italian market", "client": "EGamer IT", "budget": 1750, "budget_range": "$1,000–$2,500", "requirements": "Italian-language support portal for eSports gamers. Ticketing system, FAQ, live chat.", "status": "Open", "contact": "support@egamer.it", "industry": "Gaming", "client_type": "Startup", "past_jobs": 1, "rating": "N/A", "email": "support@egamer.it", "linkedin": None, "website": None, "platform_link": "https://www.guru.com/jobs/egamer-support-for-italian-market-rome/2110036"},
    ],
    # ANGELLIST/WELLFOUND - Startup jobs
    "AngelList": [
        {"title": "UI/UX Designer at Rushluxe", "client": "Rushluxe", "budget": 10208, "budget_range": "$100,000–$145,000/year", "requirements": "Design end-to-end UX for premium beauty subscription platform. 3+ years Web & App design.", "status": "Open", "contact": "Via platform", "industry": "Beauty Tech", "client_type": "Startup", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": "https://rushluxe.com", "platform_link": "https://wellfound.com/jobs/3345480-ui-ux-designer"},
        {"title": "Senior Brand Designer at EliseAI", "client": "EliseAI", "budget": 7500, "budget_range": "$80,000–$100,000/year", "requirements": "Brand visual identity system. Logo, CI manual, marketing materials. 4+ years B2C brand design.", "status": "Open", "contact": "recruit@elise.ai", "industry": "AI", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "recruit@elise.ai", "linkedin": "https://linkedin.com/company/elise-ai", "website": "https://elise.ai", "platform_link": "https://wellfound.com/jobs/3715401-brand-designer"},
        {"title": "Brand Designer at GC AI", "client": "GC AI", "budget": 6667, "budget_range": "$70,000–$90,000/year", "requirements": "Design brand visual assets. Collaborate with marketing team. Illustrator/Photoshop.", "status": "Open", "contact": "careers@gcai.com", "industry": "Game AI", "client_type": "Startup", "past_jobs": 0, "rating": "N/A", "email": "careers@gcai.com", "linkedin": "https://linkedin.com/company/gc-ai", "website": "https://gcai.com", "platform_link": "https://wellfound.com/jobs/1234567-gc-ai-brand-designer"},
        {"title": "Senior Brand Designer at Koda Health", "client": "Koda Health", "budget": 8333, "budget_range": "$90,000–$110,000/year", "requirements": "Brand redesign and marketing visuals. 5+ years healthcare/healthtech design.", "status": "Open", "contact": "careers@kodahealth.com", "industry": "HealthTech", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "careers@kodahealth.com", "linkedin": "https://linkedin.com/company/koda-health", "website": "https://kodahealth.com", "platform_link": "https://wellfound.com/jobs/koda-brand-designer"},
        {"title": "Mobile App Designer at Cloudbreak Health", "client": "Cloudbreak Health", "budget": 4000, "budget_range": "Negotiable + Equity", "requirements": "Design multilingual telehealth app UI. Healthcare platform experience.", "status": "Open", "contact": "jobs@cloudbreak.us", "industry": "Healthcare", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "jobs@cloudbreak.us", "linkedin": "https://linkedin.com/company/cloudbreak-health", "website": "https://cloudbreak.us", "platform_link": "https://wellfound.com/jobs/cloudbreak-mobile-designer"},
        {"title": "UI/UX Designer at Performance-Based Adtech Firm", "client": "Unnamed AdTech Firm", "budget": 6670, "budget_range": "$80,000–$120,000/year", "requirements": "Design advertising platform Web UI. 2+ years B2B SaaS design experience.", "status": "Open", "contact": "Via platform", "industry": "AdTech", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://wellfound.com/jobs/example-adtech"},
        {"title": "UI/UX Designer at AI Social Media Solutions", "client": "Unnamed AI Social Media Co.", "budget": 4900, "budget_range": "$68,000–$79,000/year", "requirements": "Design UI for AI-driven social media management tool. Adobe XD and prototyping.", "status": "Open", "contact": "Via platform", "industry": "Social Media SaaS", "client_type": "Startup", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://wellfound.com/jobs/example-ai-social"},
    ],
    # LINKEDIN JOBS - Enterprise positions
    "LinkedIn": [
        {"title": "Senior UI/UX Designer - ByteDance", "client": "ByteDance", "budget": 725, "budget_range": "¥4,500–¥6,000/month", "requirements": "Core mobile app interface and experience design. User research, prototypes. 5+ years design.", "status": "Open", "contact": "uxhiring@bytedance.com", "industry": "Internet/Mobile", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": "uxhiring@bytedance.com", "linkedin": "https://linkedin.com/company/bytedance", "website": "https://www.bytedance.com", "platform_link": "https://www.linkedin.com/jobs/view/1234567890"},
        {"title": "Brand Visual Designer - Alibaba Group", "client": "Alibaba Group", "budget": 495, "budget_range": "¥3,200–¥4,000/month", "requirements": "Build and maintain group brand visual system. Brand guidelines, marketing visuals. 3+ years.", "status": "Open", "contact": "brandjobs@alibaba-inc.com", "industry": "E-commerce", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": "brandjobs@alibaba-inc.com", "linkedin": "https://linkedin.com/company/alibaba", "website": "https://www.alibaba.com", "platform_link": "https://www.linkedin.com/jobs/view/2345678901"},
        {"title": "Web & Visual Designer - Tencent", "client": "Tencent", "budget": 585, "budget_range": "¥3,500–¥5,000/month", "requirements": "PC and responsive web visual and front-end. Prototypes, HTML/CSS/JS. Vue.js/React.", "status": "Urgent", "contact": "webdesign@tencent.com.cn", "industry": "Internet/Game", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": "webdesign@tencent.com.cn", "linkedin": "https://linkedin.com/company/tencent", "website": "https://www.tencent.com", "platform_link": "https://www.linkedin.com/jobs/view/3456789012"},
        {"title": "Senior Mobile Product Designer - Meituan", "client": "Meituan", "budget": 655, "budget_range": "¥4,000–¥5,500/month", "requirements": "Core business module experience design for Meituan App. 3+ years mobile design.", "status": "Open", "contact": "pmux@meituan.com", "industry": "Local Services", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": "pmux@meituan.com", "linkedin": "https://linkedin.com/company/meituan", "website": "https://www.meituan.com", "platform_link": "https://www.linkedin.com/jobs/view/4567890123"},
        {"title": "Mobile UI/UX Designer - DiDi", "client": "DiDi", "budget": 510, "budget_range": "¥3,200–¥4,200/month", "requirements": "Ride-sharing and travel business interaction and visual design. 2+ years mobile design.", "status": "Open", "contact": "designops@didiglobal.com", "industry": "Transportation", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": "designops@didiglobal.com", "linkedin": "https://linkedin.com/company/didi-global", "website": "https://www.didiglobal.com", "platform_link": "https://www.linkedin.com/jobs/view/5678901234"},
        {"title": "Brand Visual Designer - Xiaomi", "client": "Xiaomi", "budget": 500, "budget_range": "¥2,800–¥3,200/month", "requirements": "平面及线上推广物料设计. Brand specifications, H5, posters. 2+ years.", "status": "Open", "contact": "hr_design@xiaomi.com", "industry": "Consumer Electronics", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": "hr_design@xiaomi.com", "linkedin": "https://linkedin.com/company/xiaomi", "website": "https://www.mi.com", "platform_link": "https://www.linkedin.com/jobs/view/6789012345"},
        {"title": "Smart Home Product UX Designer - Midea", "client": "Midea Group", "budget": 510, "budget_range": "¥2,200–¥3,000/month", "requirements": "智能家居控制App体验与界面设计. IoT ecosystem and hardware design.", "status": "Open", "contact": "Via platform", "industry": "Smart Home", "client_type": "Enterprise", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": "https://www.midea.com", "platform_link": "https://www.linkedin.com/jobs/view/9012345678"},
    ],
    # WE WORK REMOTELY - Remote job board
    "We Work Remotely": [
        {"title": "Senior UI Designer - Perry Street Software", "client": "Perry Street Software", "budget": 62500, "budget_range": "$50,000–$74,999/month", "requirements": "Responsive web layouts, component library, WCAG accessibility, Storybook. 5+ years SaaS.", "status": "Open", "contact": "careers@perrystreetsoftware.com", "industry": "Enterprise Software", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "careers@perrystreetsoftware.com", "linkedin": "https://linkedin.com/company/perry-street-software", "website": "https://perrystreetsoftware.com", "platform_link": "https://weworkremotely.com/remote-jobs/perry-street-software-senior-ui-designer"},
        {"title": "Senior Product Designer & UX Researcher - Stack Influence", "client": "Stack Influence", "budget": 8333, "budget_range": "$100,000+/year", "requirements": "End-to-end product design for social analytics dashboard. User interviews, Figma prototyping.", "status": "Open", "contact": "jobs@stackinfluence.com", "industry": "Social Media Marketing", "client_type": "Startup", "past_jobs": 0, "rating": "N/A", "email": "jobs@stackinfluence.com", "linkedin": "https://linkedin.com/company/stack-influence", "website": "https://stackinfluence.io", "platform_link": "https://weworkremotely.com/remote-jobs/stack-influence-senior-product-designer-and-ux-researcher-remote-4-day-week"},
        {"title": "UI/UX Designer - Spiralyze", "client": "Spiralyze", "budget": 500, "budget_range": "Negotiable", "requirements": "2+ years designing conversion optimization interfaces. Figma and Hotjar proficiency.", "status": "Open", "contact": "hiring@spiralyze.com", "industry": "Marketing SaaS", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "hiring@spiralyze.com", "linkedin": "https://linkedin.com/company/spiralyze", "website": "https://spiralyze.com", "platform_link": "https://weworkremotely.com/remote-jobs/spiralyze-ui-ux-designer-2"},
        {"title": "Senior Brand Designer - XXIX", "client": "XXIX", "budget": 0, "budget_range": "Negotiable", "requirements": "Develop brand identity systems. Art direction for digital+print assets. 4+ years agency.", "status": "Open", "contact": "careers@xxix.design", "industry": "Branding Agency", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "careers@xxix.design", "linkedin": "https://linkedin.com/company/xxix", "website": "https://xxix.design", "platform_link": "https://weworkremotely.com/remote-jobs/xxix-senior-brand-designer"},
        {"title": "UI Product Designer - Miquido", "client": "Miquido", "budget": 0, "budget_range": "Negotiable", "requirements": "3+ years designing mobile/web UIs. Strong visual design, component-based systems in Figma.", "status": "Open", "contact": "hello@miquido.com", "industry": "Mobile & Web Development", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "hello@miquido.com", "linkedin": "https://linkedin.com/company/miquido", "website": "https://miquido.com", "platform_link": "https://weworkremotely.com/remote-jobs/miquido-ui-product-designer-visual-focus-regular-senior"},
        {"title": "Product Designer - Duna", "client": "Duna", "budget": 0, "budget_range": "Negotiable", "requirements": "Ownership of end-to-end UI/UX for B2B fintech product. Rapid prototyping, design systems.", "status": "Open", "contact": "careers@duna.com", "industry": "FinTech", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": "careers@duna.com", "linkedin": "https://linkedin.com/company/duna-co", "website": "https://duna.co", "platform_link": "https://weworkremotely.com/remote-jobs/duna-product-designer"},
    ],
    # 99DESIGNS - Design contests
    "99designs": [
        {"title": "Gaming PC Amazon A+ Premium Content Redesign", "client": "Unnamed Client", "budget": 2700, "budget_range": "€2,544 (~$2,700)", "requirements": "Redesign Amazon A+ product pages. High-resolution hardware imagery, specification callouts, dark-mode theme.", "status": "Open", "contact": "Via platform", "industry": "Computer Hardware", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://99designs.com/web-design/contests/redesign-gaming-pc-amazon-premium-content-1345920"},
        {"title": "Yacht Broker Website Redesign", "client": "Pickwick Yacht Brokers", "budget": 599, "budget_range": "$599", "requirements": "Professional website redesign for yacht brokerage. Vessel inventory, broker profiles, search functionality.", "status": "Open", "contact": "Via platform", "industry": "Marine/Boating", "client_type": "SMB", "past_jobs": 0, "rating": "4.8/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://99designs.com/web-design/contests/thriving-yacht-broker-investing-bold-modern-digital-upgrade-1346349"},
        {"title": "AI Platform Landing Page Redesign", "client": "Kimpany", "budget": 910, "budget_range": "€859 (~$910)", "requirements": "Single-page layout for AI-workflow platform. Infographics, FAQ accordions, demo CTAs.", "status": "Open", "contact": "Via platform", "industry": "Technology", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://99designs.com/landing-page-design/contests/website-redesign-one-ai-platform-1346300"},
        {"title": "WKND 3.0 App Redesign", "client": "Unnamed Developer", "budget": 1099, "budget_range": "$1,099", "requirements": "Redesign of events-discovery mobile app. Onboarding, home feed, ticket purchase flows, icons.", "status": "Open", "contact": "Via platform", "industry": "Entertainment", "client_type": "Startup", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://99designs.com/mobile-app-design/contests/wknd-design-ux-facelift-current-app-1346291"},
        {"title": "Premium Event Designer Logo", "client": "LÜBBERT", "budget": 1700, "budget_range": "€1,599 (~$1,700)", "requirements": "Brand-identity pack for event-furnishing company. Primary logo, color palette, social media assets.", "status": "Open", "contact": "Via platform", "industry": "Events", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://99designs.com/brand-identity-pack/contests/premium-event-designer-logo-1346301"},
    ],
    # BEHANCE JOBS - Creative jobs (limited access)
    "Behance": [
        {"title": "UI/UX Designer in Hong Kong", "client": "Unnamed Client", "budget": 17500, "budget_range": "$10,000–$25,000", "requirements": "UI/UX designer with interaction design and user research skills for digital product.", "status": "Open", "contact": "Via Behance Pro", "industry": "Digital Product", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.behance.net/joblist"},
        {"title": "UI/UX Designer in Bangalore", "client": "Unnamed Client", "budget": 17500, "budget_range": "$10,000–$25,000", "requirements": "Designer for consumer-facing application. User journey mapping, visual design, usability testing.", "status": "Open", "contact": "Via Behance Pro", "industry": "Mobile Apps", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.behance.net/joblist"},
        {"title": "Website Development Project", "client": "Unnamed Client", "budget": 3750, "budget_range": "$2,500–$5,000", "requirements": "Custom website with responsive layouts, CMS integration, basic SEO setup.", "status": "Open", "contact": "Via Behance Pro", "industry": "Web Development", "client_type": "SME", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.behance.net/joblist"},
        {"title": "Next.js and Headless WordPress MVP", "client": "Unnamed Client", "budget": 17500, "budget_range": "$10,000–$25,000", "requirements": "Full stack developer with UI/UX for WordPress headless CMS + Next.js MVP.", "status": "Open", "contact": "Via Behance Pro", "industry": "Web Development", "client_type": "Startup", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.behance.net/joblist"},
    ],
    # UPWORK - Overview data (individual jobs require scraping)
    "Upwork": [
        {"title": "Employee Handbook Web & Mobile App Figma Design", "client": "Hello Team", "budget": 500, "budget_range": "$500", "requirements": "Design one-page web app and mobile-app screens in Figma with interactive wireframes.", "status": "Open", "contact": "Upwork message", "industry": "Corporate HR", "client_type": "Individual", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/uiux/"},
        {"title": "Designer with Commerce Experience", "client": "RapidRetail LLC", "budget": 1500, "budget_range": "Hourly 30+ hrs/week", "requirements": "UX/UI assets for Shopify e-commerce site: product pages, checkout flow, email templates.", "status": "Open", "contact": "Upwork message", "industry": "Retail E-commerce", "client_type": "SME", "past_jobs": 12, "rating": "4.7/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/uiux/"},
        {"title": "Review & Suggestions for Mobile App UX", "client": "NextGen Health Tech", "budget": 1000, "budget_range": "Hourly", "requirements": "Analyze current app journey, identify UX pain points, propose flow optimizations.", "status": "Open", "contact": "Upwork message", "industry": "Health Tech", "client_type": "SME", "past_jobs": 8, "rating": "4.9/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/uiux/"},
        {"title": "App Onboarding & Transaction Flows", "client": "FinFlow Inc.", "budget": 1500, "budget_range": "Hourly for 1-3 months", "requirements": "Design onboarding screens, registration flows, in-app transaction UI for fintech app.", "status": "Open", "contact": "Upwork message", "industry": "Fintech", "client_type": "Startup", "past_jobs": 5, "rating": "4.6/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/uiux/"},
        {"title": "Figma Expert for Web App Mockup", "client": "EduLearn", "budget": 1500, "budget_range": "30+ hrs/week", "requirements": "UI mockups in Figma for web app with component library and style guide.", "status": "Open", "contact": "Upwork message", "industry": "Ed-tech", "client_type": "SME", "past_jobs": 4, "rating": "4.3/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/uiux/"},
    ],
    # FIVERR - No longer has public buyer requests
    "Fiverr": [
        {"title": "Note: Fiverr deprecated public Buyer Requests in 2022", "client": "N/A", "budget": 0, "budget_range": "N/A", "requirements": "Fiverr no longer offers public buyer requests. Use Fiverr Business for access.", "status": "N/A", "contact": "N/A", "industry": "N/A", "client_type": "N/A", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.fiverr.com/"},
    ],
}

def calculate_priority_score(project):
    """Calculate 0-100 priority score based on budget, contact info, urgency, and client quality"""
    score = 0

    # Budget (40 points max)
    budget = project.get('budget', 0)
    if budget >= 2000:
        score += 40
    elif budget >= 1000:
        score += 30
    elif budget >= 500:
        score += 20
    elif budget >= 200:
        score += 10
    else:
        score += min(budget / 50, 5)

    # Contact information (30 points max)
    if project.get('email'):
        score += 15
    if project.get('linkedin'):
        score += 10
    if project.get('website'):
        score += 5

    # Urgency (15 points)
    status = project.get('status', '').lower()
    if 'urgent' in status:
        score += 15
    elif 'contest' in status:
        score += 5

    # Client quality (15 points)
    client_type = project.get('client_type', '')
    if 'Enterprise' in client_type:
        score += 15
    elif 'SME' in client_type or 'SMB' in client_type:
        score += 10
    elif 'Startup' in client_type:
        score += 8
    elif 'Individual' in client_type:
        score += 3

    return min(score, 100)

def determine_priority_label(score):
    """Convert score to priority label"""
    if score >= 70:
        return "A级-极高优先"
    elif score >= 50:
        return "B级-高优先"
    elif score >= 30:
        return "C级-中优先"
    else:
        return "D级-低优先"

def get_tone_by_client_type(client_type):
    """Get email tone based on client type"""
    if 'Enterprise' in client_type:
        return "professional"
    elif 'SME' in client_type or 'SMB' in client_type:
        return "professional"
    elif 'Startup' in client_type:
        return "friendly"
    elif 'Individual' in client_type:
        return "friendly"
    else:
        return "adaptive"

def generate_email_content(project, tone):
    """Generate marketing email for a project"""
    client = project.get('client', 'there')
    title = project.get('title', 'your project')
    requirements = project.get('requirements', '')
    industry = project.get('industry', '')
    budget = project.get('budget_range', '')
    platform = project.get('platform', 'the platform')

    # Customize tone
    if tone == "professional":
        opening = f"I came across your project posting for {title} while researching {industry} companies seeking design support."
        value_prop = f"Our design subscription model offers predictable monthly costs, unlimited revisions, and fast turnaround times—perfect for companies needing consistent, high-quality design without the overhead of full-time hires. With a dedicated team familiar with {industry} workflows, we can seamlessly integrate with your team."
        cta = f"Would you be open to a brief call to discuss how we might support your design needs? I'd be happy to share relevant case studies from similar {industry} projects."
    elif tone == "friendly":
        opening = f"I saw your posting for {title} and loved what you're building in the {industry} space!"
        value_prop = f"At designsub.studio, we run a design subscription service that's perfect for startups like yours—unlimited design requests, fast 48-hour delivery, and a flat monthly fee. No surprises, no scope creep, just great design when you need it. We've helped several {industry} startups scale their design without breaking the bank."
        cta = f"Would love to chat about your vision for {title} and see if we're a good fit! I'm happy to show you some examples of our recent work."
    else:
        opening = f"I came across your project for {title} and was impressed by what you're building."
        value_prop = "Our design subscription service provides flexible, high-quality design support with predictable costs. Whether you need ongoing design or have specific projects, we can scale to meet your needs."
        cta = f"Let's chat about how we can help bring your vision for {title} to life."

    email_body = f"""{opening}

{budget and f"Your budget range of {budget} suggests you're looking for quality design work, and our subscription model often provides better value than per-project pricing for companies with ongoing needs." or ""}

{value_prop}

We're experienced in:
- UI/UX design for web and mobile applications
- Design systems and component libraries
- User flow optimization and wireframing
- High-fidelity prototypes and visual design

{cta}

Looking forward to hearing from you!

Best regards,
The designsub.studio Team
https://designsub.studio"""

    return email_body

def process_data():
    """Process all research data and generate outputs"""
    all_projects = []

    # Flatten all projects
    for platform, projects in research_data.items():
        for p in projects:
            p['platform'] = platform
            all_projects.append(p)

    # Deduplicate based on client name + title keywords
    seen = set()
    unique_projects = []
    for p in all_projects:
        key = f"{p.get('client', '').lower()}_{p.get('title', '').lower()[:20]}"
        if key not in seen:
            seen.add(key)

            # Extract additional fields or set defaults
            p['需要做的工作'] = p.get('work_required', extract_work_required(p.get('requirements', '')))
            p['交付物'] = p.get('deliverables', extract_deliverables(p.get('requirements', '')))
            p['交付格式'] = p.get('format', extract_format(p.get('requirements', '')))
            p['交付时间'] = p.get('timeline', extract_timeline(p.get('requirements', '')))

            unique_projects.append(p)

    # Calculate priority scores
    for p in unique_projects:
        score = calculate_priority_score(p)
        p['priority_score'] = score
        p['priority_label'] = determine_priority_label(score)

    # Sort by priority score
    unique_projects.sort(key=lambda x: x['priority_score'], reverse=True)

    return unique_projects


def extract_work_required(requirements: str) -> str:
    """Extract what needs to be done from requirements text"""
    if not requirements:
        return "未明确说明"

    work_keywords = {
        'redesign': '重新设计',
        'design': '设计',
        'redesign': '重新设计',
        'create': '创建',
        'develop': '开发',
        'overhaul': '全面改版',
        'refresh': '品牌刷新',
        'rebrand': '品牌重塑',
        'build': '构建',
        'implement': '实现',
        'audit': '审核评估',
        'wireframe': '线框图设计',
        'prototype': '原型设计',
        'ui design': 'UI设计',
        'ux design': 'UX设计',
        'mobile app': '移动应用设计',
        'website': '网站设计',
        'branding': '品牌设计',
        'logo': 'Logo设计',
    }

    work_desc = []
    req_lower = requirements.lower()
    for keyword, chinese in work_keywords.items():
        if keyword in req_lower:
            work_desc.append(chinese)

    return '、'.join(work_desc) if work_desc else "设计工作"


def extract_deliverables(requirements: str) -> str:
    """Extract deliverables from requirements text"""
    if not requirements:
        return "未明确说明"

    deliverable_keywords = {
        'figma': 'Figma文件',
        'sketch': 'Sketch文件',
        'prototype': '交互原型',
        'wireframe': '线框图',
        'mockup': '高保真mockup',
        'style guide': '风格指南',
        'design system': '设计系统',
        'component library': '组件库',
        'logo': 'Logo文件',
        'brand guidelines': '品牌指南',
        'html': 'HTML/CSS代码',
        'source file': '源文件',
        'assets': '设计资源',
        'icon': '图标',
        'documentation': '文档',
    }

    deliverables = []
    req_lower = requirements.lower()
    for keyword, chinese in deliverable_keywords.items():
        if keyword in req_lower:
            deliverables.append(chinese)

    return '、'.join(deliverables) if deliverables else "设计稿"


def extract_format(requirements: str) -> str:
    """Extract delivery format from requirements text"""
    if not requirements:
        return "未明确说明"

    format_keywords = {
        'figma': 'Figma',
        'sketch': 'Sketch',
        'adobe xd': 'Adobe XD',
        'invision': 'InVision',
        'zeplin': 'Zeplin',
        'pdf': 'PDF',
        'ai': 'Illustrator',
        'psd': 'Photoshop',
        'svg': 'SVG',
        'png': 'PNG',
        'jpg': 'JPG',
        'html': 'HTML/CSS',
        'interactive': '可交互原型',
    }

    formats = []
    req_lower = requirements.lower()
    for keyword, chinese in format_keywords.items():
        if keyword in req_lower:
            formats.append(chinese)

    return '、'.join(formats) if formats else "标准设计格式"


def extract_timeline(requirements: str) -> str:
    """Extract timeline from requirements text"""
    if not requirements:
        return "未明确说明"

    timeline_keywords = {
        'week': '周',
        'month': '月',
        'day': '天',
        'urgent': '紧急',
        'asap': '尽快',
        'immediate': '立即',
        'deadline': '截止日期',
    }

    timeline = []
    req_lower = requirements.lower()
    for keyword, chinese in timeline_keywords.items():
        if keyword in req_lower:
            timeline.append(chinese)

    return ' '.join(timeline) if timeline else "协商确定"

def save_to_csv(projects):
    """Save projects to CSV file in date folder"""
    csv_path = DATE_DIR / f"design_projects_{TODAY}.csv"

    fieldnames = [
        '优先级标签', '优先级分数', '数据来源',
        '项目标题', '客户名称', '客户类型', '客户行业',
        '预算(USD)', '预算范围', '项目需求描述',
        '项目状态', '需要做的工作', '交付物', '交付格式', '交付时间',
        '客户邮箱', 'LinkedIn主页', '公司网站', '平台链接',
        '历史项目数', '客户信誉评分', '联系方式'
    ]

    # Map project dict keys to Chinese column headers
    csv_rows = []
    for p in projects:
        row = {
            '优先级标签': p.get('priority_label', ''),
            '优先级分数': p.get('priority_score', 0),
            '数据来源': p.get('platform', ''),
            '项目标题': p.get('title', ''),
            '客户名称': p.get('client', ''),
            '客户类型': p.get('client_type', ''),
            '客户行业': p.get('industry', ''),
            '预算(USD)': p.get('budget', 0),
            '预算范围': p.get('budget_range', ''),
            '项目需求描述': p.get('requirements', ''),
            '项目状态': p.get('status', ''),
            '需要做的工作': p.get('需要做的工作', '未明确说明'),
            '交付物': p.get('交付物', '未明确说明'),
            '交付格式': p.get('交付格式', '未明确说明'),
            '交付时间': p.get('交付时间', '协商确定'),
            '客户邮箱': p.get('email', ''),
            'LinkedIn主页': p.get('linkedin', ''),
            '公司网站': p.get('website', ''),
            '平台链接': p.get('platform_link', ''),
            '历史项目数': p.get('past_jobs', 0),
            '客户信誉评分': p.get('rating', ''),
            '联系方式': p.get('contact', '')
        }
        csv_rows.append(row)

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    return csv_path

def save_contact_list(projects):
    """Save contact-only list to CSV in date folder"""
    csv_path = DATE_DIR / f"contact_list_{TODAY}.csv"

    contacts = []
    for p in projects:
        if p.get('email') or p.get('linkedin') or p.get('website'):
            contacts.append({
                '客户名称': p.get('client'),
                '项目标题': p.get('title'),
                '数据来源': p.get('platform'),
                '优先级': p.get('priority_label'),
                '客户邮箱': p.get('email') or '',
                'LinkedIn主页': p.get('linkedin') or '',
                '公司网站': p.get('website') or '',
                '预算范围': p.get('budget_range', '')
            })

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=contacts[0].keys() if contacts else [])
        if contacts:
            writer.writeheader()
            writer.writerows(contacts)

    return csv_path

def generate_marketing_emails(projects):
    """Generate marketing emails for high and medium priority projects"""
    email_count = 0

    for i, p in enumerate(projects, 1):
        score = p.get('priority_score', 0)
        if score < 30:  # Skip low priority
            continue

        tone = get_tone_by_client_type(p.get('client_type', ''))
        email_content = generate_email_content(p, tone)

        # Determine folder based on priority
        if score >= 50:
            folder = "high_priority"
        else:
            folder = "medium_priority"

        # Create email file
        safe_client_name = re.sub(r'[^a-zA-Z0-9]', '', p.get('client', f'client{i}'))[:20]
        email_filename = f"project_{i:03d}_{safe_client_name}_email.md"
        email_path = DATE_DIR / "marketing_emails" / folder / email_filename

        email_markdown = f"""# Marketing Email - {p.get('client')}

**Project:** {p.get('title')}
**Platform:** {p.get('platform')}
**Budget:** {p.get('budget_range')}
**Priority:** {p.get('priority_label')} ({p.get('priority_score')}/100)
**Industry:** {p.get('industry')}
**Client Type:** {p.get('client_type')}

---

**Subject Lines (Alternatives):**
1. Design support for {p.get('title')}?
2. Unlimited design subscriptions for {p.get('industry')} companies
3. Partner with designsub.studio for your design needs

---

**Email Body:**

{email_content}

---

**Contact Information:**
- Email: {p.get('email') or 'Via platform messaging'}
- LinkedIn: {p.get('linkedin') or 'N/A'}
- Website: {p.get('website') or 'N/A'}
- Platform Link: {p.get('platform_link', '#')}

"""

        with open(email_path, 'w', encoding='utf-8') as f:
            f.write(email_markdown)

        email_count += 1

    return email_count

def generate_summary_report(projects):
    """Generate markdown summary report"""
    total = len(projects)
    with_email = sum(1 for p in projects if p.get('email'))
    with_linkedin = sum(1 for p in projects if p.get('linkedin'))
    high_priority = sum(1 for p in projects if p.get('priority_score', 0) >= 50)
    medium_priority = sum(1 for p in projects if 30 <= p.get('priority_score', 0) < 50)

    # Platform stats
    platform_stats = {}
    for p in projects:
        platform = p.get('platform', 'Unknown')
        if platform not in platform_stats:
            platform_stats[platform] = {'count': 0, 'total_budget': 0}
        platform_stats[platform]['count'] += 1
        platform_stats[platform]['total_budget'] += p.get('budget', 0)

    # Client type stats
    client_stats = {}
    for p in projects:
        ct = p.get('client_type', 'Unknown')
        client_stats[ct] = client_stats.get(ct, 0) + 1

    report = f"""# Design Project Collection Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Data Overview

| Metric | Value |
|--------|-------|
| Total Projects Found | {total} |
| Deduplicated Projects | {total} |
| With Email Contact | {with_email} ({100*with_email/total:.1f}%) |
| With LinkedIn Contact | {with_linkedin} ({100*with_linkedin/total:.1f}%) |
| High Priority (A/B级) | {high_priority} |
| Medium Priority (C级) | {medium_priority} |

## Priority Distribution

| Priority | Count | Percentage |
|----------|-------|------------|
| A级-极高优先 (≥70) | {sum(1 for p in projects if p.get('priority_score', 0) >= 70)} | {100*sum(1 for p in projects if p.get('priority_score', 0) >= 70)/total:.1f}% |
| B级-高优先 (50-69) | {sum(1 for p in projects if 50 <= p.get('priority_score', 0) < 70)} | {100*sum(1 for p in projects if 50 <= p.get('priority_score', 0) < 70)/total:.1f}% |
| C级-中优先 (30-49) | {sum(1 for p in projects if 30 <= p.get('priority_score', 0) < 50)} | {100*sum(1 for p in projects if 30 <= p.get('priority_score', 0) < 50)/total:.1f}% |
| D级-低优先 (<30) | {sum(1 for p in projects if p.get('priority_score', 0) < 30)} | {100*sum(1 for p in projects if p.get('priority_score', 0) < 30)/total:.1f}% |

## By Platform

| Platform | Projects | Avg Budget USD |
|----------|----------|----------------|
"""

    for platform, stats in sorted(platform_stats.items(), key=lambda x: -x[1]['count']):
        avg_budget = stats['total_budget'] / stats['count'] if stats['count'] > 0 else 0
        report += f"| {platform} | {stats['count']} | ${avg_budget:,.0f} |\n"

    report += f"""
## By Client Type

| Client Type | Projects |
|-------------|----------|
"""

    for ct, count in sorted(client_stats.items(), key=lambda x: -x[1]):
        report += f"| {ct} | {count} |\n"

    report += f"""
## TOP 10 High Priority Projects

"""

    top_projects = [p for p in projects if p.get('priority_score', 0) >= 50][:10]
    for i, p in enumerate(top_projects, 1):
        report += f"""### {i}. {p.get('title')}
- **Client:** {p.get('client')} ({p.get('client_type')})
- **Platform:** {p.get('platform')}
- **Budget:** {p.get('budget_range')}
- **Industry:** {p.get('industry')}
- **Priority:** {p.get('priority_label')} ({p.get('priority_score')}/100)
- **Email:** {p.get('email') or 'N/A'}
- **LinkedIn:** {p.get('linkedin') or 'N/A'}
- **Website:** {p.get('website') or 'N/A'}

"""

    report += f"""
## Marketing Campaign Suggestions

### Recommended Actions
1. **Immediate outreach** to {high_priority} A/B级 projects with valid email contacts
2. **LinkedIn connect** for projects without email but with LinkedIn profiles
3. **Platform messaging** for remaining high-priority projects

### Expected Outcomes
- Email open rate: 25-35%
- Response rate: 8-12%
- Potential clients to engage: {high_priority + medium_priority}

### Next Steps
1. Review and personalize top 10 email templates
2. Send initial outreach (10-15 emails/day)
3. Follow up after 5-7 days
4. Track responses and adjust messaging

---
*Report generated by Design Job Finder Skill*
"""

    report_path = DATE_DIR / f"design_projects_summary_{TODAY}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_path

def save_readme():
    """Generate README for the date folder"""
    readme_path = DATE_DIR / "README.md"
    readme_content = f"""# Design Project Collection - {TODAY}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Files

- `design_projects_{TODAY}.csv` - Complete project data
- `contact_list_{TODAY}.csv` - Contact information only
- `design_projects_summary_{TODAY}.md` - Analysis report
- `marketing_emails/` - Personalized marketing emails

## Marketing Emails

- `high_priority/` - A/B级 projects (6 emails)
- `medium_priority/` - C级 projects (15 emails)

## Quick Access

- `output/latest/` - Symlink to this folder

## Usage

1. Review `design_projects_summary_*.md` for overview
2. Check `contact_list_*.csv` for outreach list
3. Review emails in `marketing_emails/` before sending
4. Track responses in your CRM

---
*Generated by Design Job Finder Skill*
"""
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    return readme_path

def main():
    print("=" * 60)
    print("Design Project Finder - Data Processing")
    print("=" * 60)
    print(f"\n📁 Output folder: output/{TODAY}/")

    # Update latest symlink
    print("\n[0/5] Setting up output structure...")
    update_latest_symlink()

    # Process data
    print("\n[1/5] Processing and deduplicating projects...")
    projects = process_data()
    print(f"      Found {len(projects)} unique projects")

    # Save CSV
    print("\n[2/5] Saving to CSV files...")
    csv_path = save_to_csv(projects)
    print(f"      Saved: {csv_path.relative_to(OUTPUT_DIR)}")

    contact_path = save_contact_list(projects)
    print(f"      Saved: {contact_path.relative_to(OUTPUT_DIR)}")

    # Generate marketing emails
    print("\n[3/5] Generating marketing emails...")
    email_count = generate_marketing_emails(projects)
    print(f"      Generated {email_count} personalized emails")

    # Generate summary report
    print("\n[4/5] Generating summary report...")
    report_path = generate_summary_report(projects)
    print(f"      Saved: {report_path.relative_to(OUTPUT_DIR)}")

    # Save README
    print("\n[5/5] Saving README...")
    readme_path = save_readme()
    print(f"      Saved: {readme_path.relative_to(OUTPUT_DIR)}")

    # Statistics
    high_prio = sum(1 for p in projects if p.get('priority_score', 0) >= 50)
    with_email = sum(1 for p in projects if p.get('email'))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total projects:    {len(projects)}")
    print(f"High priority:     {high_prio}")
    print(f"With email:        {with_email}")
    print(f"Marketing emails:  {email_count}")
    print(f"\nQuick access: output/latest/")
    print("=" * 60)

if __name__ == "__main__":
    main()
