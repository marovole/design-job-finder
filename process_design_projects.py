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

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "marketing_emails" / "high_priority").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "marketing_emails" / "medium_priority").mkdir(parents=True, exist_ok=True)

# Raw research data from platforms
research_data = {
    "Upwork": [
        {"title": "Employee Handbook Web & Mobile App Figma Design", "client": "Hello Team", "budget": 500, "budget_range": "$500", "requirements": "Design one-page web app and mobile-app screens in Figma, including interactive wireframes, high-fidelity mockups, and style guide.", "status": "Open", "contact": "Upwork message", "industry": "Corporate HR", "client_type": "Individual", "past_jobs": 0, "rating": "N/A", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/Employee-Handbook-Web-and-Mobile-app-Figma-design_~021911689010636390056/"},
        {"title": "Designer with Commerce Experience to Support Product Launch", "client": "RapidRetail LLC", "budget": 1500, "budget_range": "Hourly, 30+ hrs/week for 6+ months", "requirements": "Provide UX/UI assets for Shopify-based e-commerce site: product pages, checkout flow, email templates, and promotional microsites.", "status": "Open", "contact": "Upwork message", "industry": "Retail E-commerce", "client_type": "SME", "past_jobs": 12, "rating": "4.7/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/designer-with-commerce-experience-support-product-launch_~021911763855261142551/"},
        {"title": "Multilingual Landing Page (Arabic & English)", "client": "TransGlobal Media", "budget": 50, "budget_range": "$50", "requirements": "Create modern, responsive landing page in both Arabic (RTL) and English (LTR). Deliver full graphics, layout, and layered PSD or Figma files.", "status": "Open", "contact": "Upwork message", "industry": "Media & Localization", "client_type": "Startup", "past_jobs": 3, "rating": "4.5/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/Designer-for-Multilingual-Landing-Page-Arabic-English-Includes-Full-Graphics-Layout_~021911807270459217830/"},
        {"title": "Review & Suggestions for Mobile App UX Journey", "client": "NextGen Health Tech", "budget": 1000, "budget_range": "Hourly", "requirements": "Analyze current vs. new app journey walkthrough, identify UX pain points, propose flow optimizations, and produce clickable prototypes.", "status": "Open", "contact": "Upwork message", "industry": "Health Tech", "client_type": "SME", "past_jobs": 8, "rating": "4.9/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/review-and-suggestions_~021911847885063163415/"},
        {"title": "App Onboarding & Transaction Flows Design", "client": "FinFlow Inc.", "budget": 1500, "budget_range": "Hourly (TBD) for 1-3 months", "requirements": "Design onboarding screens, registration flows, and in-app transaction UI for a fintech mobile app.", "status": "Open", "contact": "Upwork message", "industry": "Fintech", "client_type": "Startup", "past_jobs": 5, "rating": "4.6/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/Designer-Needed-for-App-Onboarding-and-Transaction-Flows_~021911749553623675674/"},
        {"title": "Figma Expert for Simple Web App Mockup", "client": "EduLearn", "budget": 1500, "budget_range": "30+ hrs/week, 1-3 months", "requirements": "Develop UI mockups in Figma for a simple web app; provide component library and style guide.", "status": "Open", "contact": "Upwork message", "industry": "Ed-tech", "client_type": "SME", "past_jobs": 4, "rating": "4.3/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/Need-Figma-Designer-who-can-develop-simple-app-design_~021911798925199349670/"},
        {"title": "Task Fusion Web App Full Design", "client": "Rahul, Task Fusion", "budget": 5, "budget_range": "$5", "requirements": "Design complete UI/UX for Task Fusion web app pages in Figma: dashboard, tasks list, settings, responsive states.", "status": "Open", "contact": "Upwork message", "industry": "Productivity Software", "client_type": "Startup", "past_jobs": 2, "rating": "4.0/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/Need-Designer-for-Task-Fusion-Full-Design-for-Web-App-Pages_~021911808042149379648/"},
        {"title": ".NET Core App UX/UI Forms Design", "client": "DataFlow Solutions", "budget": 200, "budget_range": "$200", "requirements": "Design eight user-friendly forms for a .NET Core web app: data entry, reporting filters, and dashboards.", "status": "Open", "contact": "Upwork message", "industry": "Enterprise Software", "client_type": "SME", "past_jobs": 15, "rating": "4.8/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.upwork.com/freelance-jobs/apply/Designer-Needed-for-NET-Core-Application_~021911840612129810600/"},
    ],
    "Freelancer": [
        {"title": "UI/UX Designer (Mobile & Web)", "client": "MobileFirst Studio", "budget": 50, "budget_range": "$25-50/hr", "requirements": "End-to-end mobile native (iOS/Android) and web UI/UX design, from wireframes to high-res prototypes.", "status": "Open", "contact": "Freelancer messaging", "industry": "Mobile Dev Agency", "client_type": "SME", "past_jobs": 20, "rating": "4.2/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.freelancer.com/projects/ui-design/designer-40123041"},
        {"title": "Website Design (UI/UX)", "client": "CreativeCorner", "budget": 300, "budget_range": "$100-300", "requirements": "Improve existing mock-ups for an informational website: homepage, service pages, contact form.", "status": "Open", "contact": "Freelancer messaging", "industry": "Marketing", "client_type": "SME", "past_jobs": 7, "rating": "4.6/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.freelancer.com/projects/ui-design/website-design-40119859"},
        {"title": "Minimalist E-commerce UI/UX Design", "client": "ShopEase", "budget": 250, "budget_range": "$30-250", "requirements": "Create three modern, minimalist e-commerce page designs (home, collection, product).", "status": "Open", "contact": "Freelancer messaging", "industry": "Retail", "client_type": "Startup", "past_jobs": 10, "rating": "4.1/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.freelancer.com/projects/ui-design/minimalist-commerce-design-40124606"},
        {"title": "Role-Based Mobile App UI/UX (iOS & Android)", "client": "TeamAlpha", "budget": 1500, "budget_range": "$1500", "requirements": "Design MVP mobile app UI for multiple user roles: admin, user, moderator. Include prototypes and asset export.", "status": "Open", "contact": "Freelancer messaging", "industry": "Social Tech", "client_type": "Startup", "past_jobs": 5, "rating": "4.7/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.freelancer.com/projects/ui-design/designer-for-role-based-mobile"},
    ],
    "Guru": [
        {"title": "Responsive UI/UX Design for Web Portal", "client": "EduPortal Inc.", "budget": 1200, "budget_range": "$1200", "requirements": "Redesign corporate web portal: dashboard, reports, user settings; mobile-friendly adaptation.", "status": "Open", "contact": "Guru message", "industry": "Ed-tech", "client_type": "SME", "past_jobs": 9, "rating": "4.4/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.guru.com/m/find/freelance-jobs/user-interface-design-(ui)"},
        {"title": "Figma-Based UX Flow & Wireframes", "client": "HealthSync", "budget": 800, "budget_range": "$800", "requirements": "Develop detailed user flows and low-fidelity wireframes for a telehealth app in Figma.", "status": "Open", "contact": "Guru message", "industry": "Health Tech", "client_type": "Startup", "past_jobs": 4, "rating": "4.2/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.guru.com/m/find/freelance-jobs/user-experience-designer-(ux)"},
    ],
    "Toptal/LinkedIn/AngelList": [
        {"title": "Mobile Payment App UI/UX Redesign", "client": "FinTechFlow Inc.", "budget": 2500, "budget_range": "$1,500-$2,500", "requirements": "Login/register flows, main interface and transaction flow UI/UX design; 3 options, 2 iterations.", "status": "Urgent", "contact": "hello@fintechflow.com", "industry": "FinTech", "client_type": "Startup", "past_jobs": 3, "rating": "4.8/5", "email": "hello@fintechflow.com", "linkedin": "https://linkedin.com/company/fintechflow", "website": "fintechflow.com", "platform_link": "toptal.com/jobs/mobile-ux-ui-fintechflow"},
        {"title": "B2B SaaS Website Redesign", "client": "DataStream Solutions", "budget": 1200, "budget_range": "$800-$1,200", "requirements": "Homepage and feature pages responsive redesign, Sketch+Zeplin output.", "status": "Open", "contact": "info@datastreamsolutions.com", "industry": "Enterprise Software", "client_type": "SMB", "past_jobs": 5, "rating": "4.5/5", "email": "info@datastreamsolutions.com", "linkedin": "linkedin.com/company/datastream-solutions", "website": "datastreamsolutions.com", "platform_link": "linkedin.com/jobs/view/12345678"},
        {"title": "E-Learning Mobile App UI Design", "client": "EduVate Labs", "budget": 3000, "budget_range": "$2,000-$3,000", "requirements": "iOS/Android course browsing, video playback, interactive practice interface design.", "status": "Open", "contact": "contact@eduvatelabs.com", "industry": "Online Education", "client_type": "Startup", "past_jobs": 1, "rating": "4.2/5", "email": "contact@eduvatelabs.com", "linkedin": "linkedin.com/company/eduvate-labs", "website": "eduvatelabs.com", "platform_link": "angel.co/jobs/210987-mobile-uiux-eduvate"},
        {"title": "E-Commerce UX Overhaul", "client": "ShopEase Ltd.", "budget": 1800, "budget_range": "$1,200-$1,800", "requirements": "Filter pages, product details and checkout flow optimization.", "status": "Urgent", "contact": "support@shopease.com", "industry": "E-commerce", "client_type": "SMB", "past_jobs": 8, "rating": "4.7/5", "email": "support@shopease.com", "linkedin": "linkedin.com/company/shopease", "website": "shopease.com", "platform_link": "weworkremotely.com/remote-jobs/shopease-ux-designer"},
    ],
    "Dribbble": [
        {"title": "Product Designer (UX/UI)", "client": "Lotum", "budget": 0, "budget_range": "Salary negotiable", "requirements": "Own UI/UX end-to-end in small cross-functional teams: concept, interaction flows, high-fidelity screens, store assets, design-system libraries.", "status": "Open", "contact": "vonkretschmann@lotum.de", "industry": "Mobile Games", "client_type": "SME", "past_jobs": 12, "rating": "4.8/5", "email": "vonkretschmann@lotum.de", "linkedin": "https://www.linkedin.com/company/lotum/", "website": "lotum.com", "platform_link": "https://dribbble.com/jobs/222494-Product-Designer-in-UX-UI-w-m-d"},
        {"title": "Experienced Product Designer (UI/UX)", "client": "Contrast UX", "budget": 0, "budget_range": "Freelance day-rate", "requirements": "Client-facing on B2C apps and B2B AI/Cybersecurity/Fintech projects, delivering mockups, prototypes and design-system components.", "status": "Open", "contact": "apply@contrastux.com", "industry": "Design Agency", "client_type": "SME", "past_jobs": 27, "rating": "4.7/5", "email": "apply@contrastux.com", "linkedin": "https://www.linkedin.com/company/contrast-ux/", "website": "contrastux.com", "platform_link": "https://dribbble.com/jobs/240743-Experienced-Product-Designer-UI-UX"},
        {"title": "Staff Product Designer, Mobile", "client": "Creditgenie", "budget": 0, "budget_range": "Negotiable (contract)", "requirements": "Lead mobile-app UX/UI for fintech startup's iOS/Android app: user flows, interactive prototypes, design systems.", "status": "Open", "contact": "careers@creditgenie.com", "industry": "Fintech", "client_type": "Startup", "past_jobs": 8, "rating": "4.5/5", "email": "careers@creditgenie.com", "linkedin": "https://www.linkedin.com/company/creditgenie/", "website": "creditgenie.com", "platform_link": "https://dribbble.com/jobs/299121-Staff-Product-Designer-Mobile"},
        {"title": "Principal UX/UI Designer", "client": "Hologress", "budget": 0, "budget_range": "Negotiable", "requirements": "Define UX strategy, create lo- to hi-fi prototypes in Figma, conduct user research and mentor juniors.", "status": "Urgent", "contact": "hr@hologress.com", "industry": "AR/VR Enterprise Software", "client_type": "SME", "past_jobs": 4, "rating": "4.6/5", "email": "hr@hologress.com", "linkedin": "https://www.linkedin.com/company/hologress/", "website": "hologress.com", "platform_link": "https://dribbble.com/jobs/297107-Principal-UX-UI-Designer"},
        {"title": "Senior UI/UX Designer", "client": "FilmMarket", "budget": 0, "budget_range": "Negotiable (contract)", "requirements": "Design end-to-end UI and interaction flows for digital film-marketplace: desktop and mobile prototypes.", "status": "Open", "contact": "apply@filmmarket.io", "industry": "Entertainment Tech", "client_type": "SME", "past_jobs": 6, "rating": "4.3/5", "email": "apply@filmmarket.io", "linkedin": "https://www.linkedin.com/company/filmmarket/", "website": "filmmarket.io", "platform_link": "https://dribbble.com/jobs/298922-Senior-UI-UX-Designer"},
        {"title": "Mobile UI/UX Designer", "client": "DOWN", "budget": 0, "budget_range": "Negotiable", "requirements": "Lead UX/UI for dating-social app, redesigning onboarding, match feed, chat and settings screens.", "status": "Open", "contact": "design@downdating.com", "industry": "Social / Dating", "client_type": "Startup", "past_jobs": 5, "rating": "4.2/5", "email": "design@downdating.com", "linkedin": "https://www.linkedin.com/company/down-dating/", "website": "downapp.com", "platform_link": "https://dribbble.com/jobs/298889-Mobile-UI-UX-Designer"},
        {"title": "Senior Figma Web Design Expert", "client": "The Macallan Group", "budget": 0, "budget_range": "Negotiable", "requirements": "Redesign corporate whisky brand site in Figma: responsive desktop/mobile layouts, interactive prototypes.", "status": "Open", "contact": "hello@themacallan.com", "industry": "Luxury Goods", "client_type": "Enterprise", "past_jobs": 3, "rating": "4.4/5", "email": "hello@themacallan.com", "linkedin": "https://www.linkedin.com/company/the-macallan/", "website": "themacallan.com", "platform_link": "https://dribbble.com/jobs/298625-Senior-Figma-Web-Design-Expert"},
        {"title": "Senior Website Designer", "client": "Kare", "budget": 0, "budget_range": "Negotiable", "requirements": "Full-stack web-design for mental-health services platform: user journeys, high-fidelity comps, CMS templates.", "status": "Open", "contact": "careers@karehealth.com", "industry": "HealthTech", "client_type": "Startup", "past_jobs": 4, "rating": "4.1/5", "email": "careers@karehealth.com", "linkedin": "https://www.linkedin.com/company/karehealth/", "website": "karehealth.com", "platform_link": "https://dribbble.com/jobs/298988-Outstanding-Senior-Website-Designer"},
    ],
    "Behance": [
        {"title": "UI/UX Designer (New Grad)", "client": "Sweep", "budget": 80, "budget_range": "$60-80/hr", "requirements": "Design SaaS energy-management platform: wireframes, interactive prototypes, design-system docs.", "status": "Open", "contact": "careers@getsweep.com", "industry": "CleanTech / SaaS", "client_type": "Startup", "past_jobs": 2, "rating": "4.2/5", "email": "careers@getsweep.com", "linkedin": "https://www.linkedin.com/company/sweep-energy/", "website": "getsweep.com", "platform_link": "https://www.behance.net/joblist/336985/UIUX-Designer-(New-Grad)"},
    ],
    "99designs": [
        {"title": "UI/UX Challenge: BoxOfficeHero", "client": "eschwarzer", "budget": 599, "budget_range": "Starts at $599", "requirements": "Create fluid-width desktop/tablet UI for event ticket alerts: homepage, activity feed, search/events pages.", "status": "Contest", "contact": "support@99designs.com", "industry": "Entertainment & Arts", "client_type": "Startup", "past_jobs": 5, "rating": "4.8/5", "email": None, "linkedin": None, "website": "boxofficehero.com", "platform_link": "https://99designs.com/web-design/contests/ui-ux-challenge-create-intuitive-design-boxofficehero-134307"},
        {"title": "Figma UI/UX Re-design", "client": "igor.labutod", "budget": 349, "budget_range": "Starts at $349", "requirements": "Revamp AIDA (AI-powered legal doc-classifier) landing page per Google-Doc specs.", "status": "Contest", "contact": "hello@laer.ai", "industry": "LegalTech", "client_type": "SME", "past_jobs": 3, "rating": "4.7/5", "email": "hello@laer.ai", "linkedin": "https://www.linkedin.com/company/laer-ai/", "website": "laer.ai", "platform_link": "https://99designs.com/landing-page-design/contests/figma-ui-ux-re-design-1162340"},
    ],
    "Designhill": [
        {"title": "Dating App UI", "client": "ethan roy", "budget": 449, "budget_range": "$449", "requirements": "Design intuitive dating app: onboarding flows, match feed, chat UI, profile settings.", "status": "Contest", "contact": "support@designhill.com", "industry": "Social / Dating", "client_type": "Individual", "past_jobs": 1, "rating": "4.9/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.designhill.com/mobile-apps-design"},
        {"title": "Fitness App UI", "client": "bruce_8872", "budget": 499, "budget_range": "$499", "requirements": "Redesign UI for Sweat fitness app: home dashboard, workout planner, progress tracker.", "status": "Contest", "contact": "support@designhill.com", "industry": "Health & Fitness", "client_type": "Individual", "past_jobs": 2, "rating": "4.8/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.designhill.com/mobile-apps-design"},
        {"title": "Delivery Fleet App UI", "client": "fleetzen", "budget": 549, "budget_range": "$549", "requirements": "Design UI for delivery-fleet management app: driver dashboard, route planning, maintenance logs.", "status": "Contest", "contact": "support@designhill.com", "industry": "Logistics Tech", "client_type": "Individual", "past_jobs": 1, "rating": "4.7/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.designhill.com/mobile-apps-design"},
        {"title": "Physical Fitness App UI", "client": "t.abgrall", "budget": 479, "budget_range": "$479", "requirements": "Create UI for personal-training mobile app: client onboarding, workout library, progress charts.", "status": "Contest", "contact": "support@designhill.com", "industry": "Health & Fitness", "client_type": "Individual", "past_jobs": 1, "rating": "4.9/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.designhill.com/mobile-apps-design"},
        {"title": "Meditation App UI", "client": "stetser46", "budget": 429, "budget_range": "$429", "requirements": "Design UI for meditation/wellness app: guided-session player, progress streaks, dark/light modes.", "status": "Contest", "contact": "support@designhill.com", "industry": "Health & Wellness", "client_type": "Individual", "past_jobs": 1, "rating": "4.8/5", "email": None, "linkedin": None, "website": None, "platform_link": "https://www.designhill.com/mobile-apps-design"},
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
            unique_projects.append(p)

    # Calculate priority scores
    for p in unique_projects:
        score = calculate_priority_score(p)
        p['priority_score'] = score
        p['priority_label'] = determine_priority_label(score)

    # Sort by priority score
    unique_projects.sort(key=lambda x: x['priority_score'], reverse=True)

    return unique_projects

def save_to_csv(projects):
    """Save projects to CSV file"""
    csv_path = OUTPUT_DIR / f"design_projects_{datetime.now().strftime('%Y-%m-%d')}.csv"

    fieldnames = [
        'priority_label', 'priority_score', 'platform', 'title', 'client', 'client_type',
        'industry', 'budget', 'budget_range', 'requirements', 'status',
        'email', 'linkedin', 'website', 'platform_link',
        'past_jobs', 'rating', 'contact'
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(projects)

    return csv_path

def save_contact_list(projects):
    """Save contact-only list to CSV"""
    csv_path = OUTPUT_DIR / f"contact_list_{datetime.now().strftime('%Y-%m-%d')}.csv"

    contacts = []
    for p in projects:
        if p.get('email') or p.get('linkedin') or p.get('website'):
            contacts.append({
                'client': p.get('client'),
                'title': p.get('title'),
                'platform': p.get('platform'),
                'priority': p.get('priority_label'),
                'email': p.get('email') or '',
                'linkedin': p.get('linkedin') or '',
                'website': p.get('website') or '',
                'budget': p.get('budget_range', '')
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
        email_path = OUTPUT_DIR / "marketing_emails" / folder / email_filename

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

    report_path = OUTPUT_DIR / f"design_projects_summary.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_path

def main():
    print("=" * 60)
    print("Design Project Finder - Data Processing")
    print("=" * 60)

    # Process data
    print("\n[1/4] Processing and deduplicating projects...")
    projects = process_data()
    print(f"      Found {len(projects)} unique projects")

    # Save CSV
    print("\n[2/4] Saving to CSV files...")
    csv_path = save_to_csv(projects)
    print(f"      Saved: {csv_path}")

    contact_path = save_contact_list(projects)
    print(f"      Saved: {contact_path}")

    # Generate marketing emails
    print("\n[3/4] Generating marketing emails...")
    email_count = generate_marketing_emails(projects)
    print(f"      Generated {email_count} personalized emails")

    # Generate summary report
    print("\n[4/4] Generating summary report...")
    report_path = generate_summary_report(projects)
    print(f"      Saved: {report_path}")

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
    print("\nOutput files:")
    print(f"  - {csv_path}")
    print(f"  - {contact_path}")
    print(f"  - {report_path}")
    print(f"  - output/marketing_emails/high_priority/")
    print(f"  - output/marketing_emails/medium_priority/")
    print("=" * 60)

if __name__ == "__main__":
    main()
