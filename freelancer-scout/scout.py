#!/usr/bin/env python3
"""
Freelancer Scout - One Person Army Edition
"""
import json
import asyncio
import logging
import os
import requests
from typing import List
from dotenv import load_dotenv

from hybrid_analyzer import analyze_project, ProjectAnalysis, ProjectStage
from outreach_generator import generate_email
from realtime_verifier import RealtimeVerifier, VerificationConfig

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scout")

def search_exa(query: str, api_key: str, num_results: int = 10) -> List[dict]:
    """Search for projects using Exa API"""
    url = "https://api.exa.ai/search"

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "numResults": num_results,
        "contents": {
            "text": True,
            "highlights": True
        }
    }

    print(f"📡 Searching Exa for: '{query}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        logger.error(f"Exa API Error: {response.text}")
        return []

    data = response.json()
    projects = []

    for res in data.get("results", []):
        # Heuristic to find client name from title or domain
        client_name = res.get("title", "").split(" - ")[0]

        projects.append({
            "title": res.get("title", "Untitled Project"),
            "description": res.get("text", "")[:1000], # Truncate for analysis
            "requirements": "\n".join(res.get("highlights", [])),
            "client": client_name,
            "website": res.get("url", ""),
            "id": res.get("id", "")
        })

    print(f"✅ Found {len(projects)} results.")
    return projects

def search_brave(query: str, api_key: str, num_results: int = 10, freshness: str = None) -> List[dict]:
    """Search for projects using Brave Search API"""
    url = "https://api.search.brave.com/res/v1/web/search"

    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json"
    }

    params = {
        "q": query,
        "count": min(num_results, 20), # Brave max per page is 20
        "result_filter": "web",
    }

    if freshness:
        # pd = Past Day, pw = Past Week, pm = Past Month
        params["freshness"] = freshness

    print(f"🦁 Searching Brave for: '{query}' (Freshness: {freshness or 'Any'})...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        logger.error(f"Brave API Error: {response.text}")
        return []

    data = response.json()
    projects = []

    for res in data.get("web", {}).get("results", []):
        client_name = res.get("title", "").split(" - ")[0]

        # Combine snippet and extra snippets for context
        description = res.get("description", "")
        if res.get("extra_snippets"):
            description += "\n" + "\n".join(res.get("extra_snippets"))

        projects.append({
            "title": res.get("title", "Untitled Project"),
            "description": description,
            "requirements": description, # Brave snippets are short, so we reuse description
            "client": client_name,
            "website": res.get("url", ""),
            "id": res.get("id", res.get("url")) # Use URL as ID if no ID
        })

    print(f"✅ Found {len(projects)} results via Brave.")
    return projects

TEST_PROJECTS = [
    {
        "title": "Need help building an MVP for a pet sitting app",
        "description": "I have an idea for a dog walking uber. Need someone to build the app.",
        "requirements": "iOS and Android. I don't have specs yet.",
        "client": "DogWalker Inc",
        "email": "test@example.com"
    },
    {
        "title": "Fix bugs in our legacy Django backend",
        "description": "Our current dev left and the code is a mess.",
        "requirements": "Python, Django, PostgreSQL. Need it fixed ASAP.",
        "client": "Legacy Corp",
        "email": "admin@legacy.com"
    },
    {
        "title": "Looking for UI Designer",
        "description": "Need a figma design for a landing page.",
        "requirements": "Figma, Sketch. No coding required.",
        "client": "DesignAgency",
        "email": "design@agency.com"
    }
]

async def process_projects(projects: List[dict]):
    print(f"🔍 Scouting {len(projects)} projects...")

    verifier = RealtimeVerifier(VerificationConfig.quick())

    results = []

    for p in projects:
        # 1. Verify
        v_result = await verifier.verify_project(p)
        if not v_result.is_valid and v_result.email_result and v_result.email_result.is_invalid:
            logger.warning(f"Skipping {p['title']} - Invalid Contact")
            continue

        # 2. Analyze
        analysis = analyze_project(p)

        # 3. Score/Filter
        score = 0
        if analysis.is_fuzzy: score += 5
        if analysis.project_stage == ProjectStage.GREENFIELD: score += 3
        if len(analysis.dev_needs) > 0 and len(analysis.pm_needs) > 0: score += 4
        if 'missing_cto' in analysis.pain_points: score += 5

        # Filter out pure design jobs if we want (optional)
        if len(analysis.dev_needs) == 0 and len(analysis.pm_needs) == 0:
            score -= 10

        results.append((score, analysis, p))

    # Sort by score
    results.sort(key=lambda x: x[0], reverse=True)

    print("\n🏆 Top Matches:")
    for score, analysis, p in results:
        if score < 0: continue

        print(f"\n[Score: {score}] {analysis.project_title}")
        print(f"Stage: {analysis.project_stage.value}")
        print(f"Pain Points: {', '.join(analysis.pain_points)}")

        # Generate Email
        email = generate_email(analysis)
        print("-" * 40)
        print("📧 Generated Draft:")
        print(email.strip())
        print("-" * 40)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run with test data")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--api-key", type=str, help="API Key for the selected provider")
    parser.add_argument("--provider", choices=['exa', 'brave'], default='exa', help="Search provider (default: exa)")
    parser.add_argument("--freshness", choices=['pd', 'pw', 'pm'], help="Brave freshness (pd=Day, pw=Week, pm=Month)")
    args = parser.parse_args()

    if args.test:
        asyncio.run(process_projects(TEST_PROJECTS))
    elif args.query:
        projects = []

        if args.provider == 'exa':
            api_key = args.api_key or os.environ.get("EXA_API_KEY")
            if not api_key:
                print("❌ Error: Exa API Key required. Use --api-key or set EXA_API_KEY.")
                return
            projects = search_exa(args.query, api_key)

        elif args.provider == 'brave':
            api_key = args.api_key or os.environ.get("BRAVE_API_KEY")
            if not api_key:
                print("❌ Error: Brave API Key required. Use --api-key or set BRAVE_API_KEY.")
                return
            projects = search_brave(args.query, api_key, freshness=args.freshness)

        if projects:
            asyncio.run(process_projects(projects))
    else:
        print("Usage: python3 scout.py --test OR --query 'looking for mvp' --provider brave --freshness pw")

if __name__ == "__main__":
    main()
