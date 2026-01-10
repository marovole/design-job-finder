#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Marketing Email Generator for Design Job Finder
为高匹配度项目生成个性化的 AI 营销邮件

Features:
- 远程工作优先 (Remote-first)
- 时区友好 (UTC+8 - China/Singapore)
- 兼职/项目合作类型自动检测
- 邮件沟通为主，拒绝电话

Usage:
    python3 generate_ai_emails.py

Output:
    output/latest/marketing_emails/ai_generated/
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Paths
OUTPUT_DIR = Path("output")
LATEST_DIR = OUTPUT_DIR / "latest"
AI_EMAILS_DIR = LATEST_DIR / "marketing_emails" / "ai_generated"

# User profile for email personalization
USER_PROFILE = {
    "name": "Rong Huang (黄蓉)",
    "name_en": "Rong Huang",
    "role": "Senior UX Designer / Product Manager",
    "website": "https://hueshadow.com",
    "email": "hueshadow989@gmail.com",
    "linkedin": "https://www.linkedin.com/in/ronn-huang-7b50273a3/",
    "years_experience": 10,
    "company": "Huawei",
    "timezone": "UTC+8 (China/Singapore)",
    "location": "Suzhou/Shanghai, China",
    "communication_preference": "Email-based asynchronous communication preferred",
    "no_phone": True,
    "highlight_projects": [
        {
            "name": "HUAWEI Analytics",
            "benchmark": "Google Analytics",
            "result_en": "21,000+ apps integrated globally, 15,520+ overseas"
        },
        {
            "name": "Business Connect",
            "benchmark": "Google My Business",
            "result_en": "5.94 million merchants, 110 content providers"
        },
        {
            "name": "华为云费用中心",
            "result_en": "Enterprise cloud billing system"
        }
    ]
}


# Part-time / Project-based work type keywords
WORK_TYPE_KEYWORDS = {
    "part_time": ["part-time", "part time", "freelance", "freelancer", "hourly", "per hour", "flexible hours"],
    "project_based": ["project", "contract", "one-time", "fixed price", "fixed-price", "短周期", "单次项目"],
    "remote": ["remote", "work from home", "wfh", "anywhere", "global", "worldwide", "distributed"],
    "no_phone": ["no calls", "no phone", "async", "asynchronous", "email only"]
}


def detect_work_type(project: Dict) -> Dict:
    """Detect work type from project requirements"""
    requirements = project.get('requirements', '').lower()
    title = project.get('title', '').lower()
    budget = project.get('budget_range', '').lower()
    combined = f"{requirements} {title} {budget}"

    work_type = {
        "is_part_time": False,
        "is_project_based": False,
        "is_remote": True,  # Default to remote
        "work_type_label": "Remote/Freelance",
        "needs_communication_note": False
    }

    # Detect part-time
    for kw in WORK_TYPE_KEYWORDS["part_time"]:
        if kw in combined:
            work_type["is_part_time"] = True
            work_type["needs_communication_note"] = True
            break

    # Detect project-based
    for kw in WORK_TYPE_KEYWORDS["project_based"]:
        if kw in combined:
            work_type["is_project_based"] = True
            work_type["needs_communication_note"] = True
            break

    # Detect remote
    for kw in WORK_TYPE_KEYWORDS["remote"]:
        if kw in combined:
            work_type["is_remote"] = True
            break

    # Set work type label
    if work_type["is_part_time"] and work_type["is_project_based"]:
        work_type["work_type_label"] = "Part-time/Project"
    elif work_type["is_part_time"]:
        work_type["work_type_label"] = "Part-time/Freelance"
    elif work_type["is_project_based"]:
        work_type["work_type_label"] = "Project-based/Contract"
    else:
        work_type["work_type_label"] = "Remote/Freelance"

    return work_type


def get_communication_note(work_type: Dict) -> str:
    """Get communication preference note for part-time/project work"""
    if not work_type["needs_communication_note"]:
        return ""

    return f"""
**Communication:**
I'm based in China (UTC+8) and prefer email-based communication for this {work_type['work_type_label']} role. Happy to discuss project details via email exchange."""


def get_timezone_info() -> str:
    """Get timezone and availability information"""
    return """
**Timezone & Availability:**
- Location: Suzhou/Shanghai, China (UTC+8)
- Available for async collaboration across timezones
- Can accommodate 2-4 hours of overlap with US timezones (e.g., 6PM-10PM China time)"""


def select_highlight_for_project(project: Dict) -> Dict:
    """Select the most relevant highlight project based on requirements"""
    requirements = project.get('requirements', '').lower()
    title = project.get('title', '').lower()
    industry = project.get('industry', '').lower()
    combined = f"{requirements} {title} {industry}"

    highlights = USER_PROFILE['highlight_projects']

    # Priority keywords for each highlight
    highlight_keywords = {
        "HUAWEI Analytics": ["dashboard", "analytics", "data", "visualization", "tracking", "metrics", "reporting", "monitoring"],
        "Business Connect": ["merchant", "business", "commerce", "local", "listing", "directory"],
        "华为云费用中心": ["cloud", "billing", "payment", "subscription", "invoice", "cost", "finance"]
    }

    # Find best match
    best_match = None
    best_score = 0

    for highlight in highlights:
        name = highlight.get('name', '')
        keywords = highlight_keywords.get(name, [])
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_match = highlight

    # Return best match or first one as default
    return best_match or highlights[0] if highlights else None


def get_tone_by_client_type(client_type: str) -> str:
    """Determine email tone based on client type"""
    client_type = client_type.lower() if client_type else ""
    if 'enterprise' in client_type:
        return "professional and formal"
    elif 'sme' in client_type or 'smb' in client_type:
        return "professional yet warm"
    elif 'startup' in client_type:
        return "friendly and enthusiastic"
    else:
        return "professional and warm"


def generate_subject_lines(project: Dict, highlight: Dict) -> List[str]:
    """Generate 3 alternative subject lines with 【求职】 prefix"""
    title = project.get('title', 'design role')
    industry = project.get('industry', '')
    client = project.get('client', '')

    subjects = [
        f"【求职】UX Expertise for {title} at {client}",
        f"【求职】Enterprise Design Leadership for {industry} Company",
        f"【求职】Design Subscription for {client}"
    ]

    # Add industry-specific subject if applicable
    if 'analytics' in industry.lower() or 'data' in industry.lower():
        subjects.insert(0, f"【求职】Data Visualization & Dashboard Design")

    return subjects[:3]


def create_email_prompt(project: Dict, highlight: Dict) -> str:
    """Create the LLM prompt for email generation"""
    tone = get_tone_by_client_type(project.get('client_type', ''))

    prompt = f"""You are Rong Huang, a Senior UX Designer with 10 years of experience at Huawei, writing a personalized outreach email.

**About Rong Huang:**
- 10 years UX design experience, 6 years at Huawei
- Led HUAWEI Analytics (compared to Google Analytics) serving 21,000+ apps globally
- Led Business Connect (compared to Google My Business) serving 5.94 million merchants
- Expertise: B2B/SaaS, dashboard design, analytics, enterprise systems, design systems

**About the Client's Project:**
- Company: {project.get('client', 'N/A')}
- Role: {project.get('title', 'N/A')}
- Industry: {project.get('industry', 'N/A')}
- Platform: {project.get('platform', 'N/A')}
- Budget: {project.get('budget_range', 'N/A')}
- Requirements: {project.get('requirements', 'N/A')}

**Relevant Experience to Reference:**
- {highlight.get('name', 'Relevant Project')}: {highlight.get('result_en', 'N/A')}

**Match Reasons:**
{chr(10).join(f'- {r}' for r in project.get('match_reasons', []))}

**Instructions:**
Write a {tone} personalized outreach email (120-180 words) in English:

1. **Opening (2-3 sentences):**
   - Mention you found their {project.get('title', 'role')} on {project.get('platform', 'the platform')}
   - Reference the relevant Huawei project ({highlight.get('name', 'experience')}) with specific metrics
   - Show genuine understanding of their needs

2. **Value Proposition (3-4 sentences):**
   - Connect your Huawei experience to their specific requirements
   - Emphasize B2B/SaaS, dashboard, enterprise expertise
   - Mention design subscription model as flexible alternative

3. **Call to Action (1-2 sentences):**
   - Invite to view portfolio: https://hueshadow.com
   - Suggest a brief call or video meeting

4. **Signature:**
   Rong Huang (黄蓉)
   Senior UX Designer | Product Manager
   Portfolio: https://hueshadow.com
   LinkedIn: https://www.linkedin.com/in/ronn-huang-7b50273a3/

**Requirements:**
- Avoid generic template language
- Use specific numbers and achievements from Huawei experience
- Sound genuine and professional, not salesy
- Maximum 180 words, minimum 120 words
- Output ONLY the email body with subject lines marked

Output format:
---
Subject: [Your chosen subject line]

[Email body here]

---
"""
    return prompt


def generate_email_with_claude(prompt: str) -> tuple:
    """
    Generate email using Claude CLI or API
    Returns: (subject_lines, email_body)
    """
    try:
        # Try using Claude Code CLI if available
        import subprocess

        # Create a system prompt for Claude
        full_prompt = f"""{prompt}

Generate the email now. Return ONLY:
1. A subject line starting with "Subject:"
2. The email body

Do not include any explanations or additional text."""

        result = subprocess.run(
            ["claude", "-p", full_prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            output = result.stdout
            # Parse the output
            lines = output.strip().split('\n')
            subject_lines = []
            email_body_lines = []
            in_body = False

            for line in lines:
                if line.startswith('Subject:'):
                    subject_lines.append(line.replace('Subject:', '').strip())
                elif '---' in line:
                    in_body = not in_body
                elif in_body or not line.startswith('Subject'):
                    email_body_lines.append(line)

            email_body = '\n'.join(email_body_lines).strip()
            return subject_lines if subject_lines else ["Re: Your Design Needs"], email_body

    except Exception as e:
        print(f"  Note: Claude CLI not available ({e})")
        print("  Falling back to template-based generation...")

    return None, None


def generate_template_email(project: Dict, highlight: Dict) -> tuple:
    """Generate a template-based email as fallback with work type awareness"""
    tone = get_tone_by_client_type(project.get('client_type', ''))
    client = project.get('client', 'Team')
    title = project.get('title', 'design role')
    platform = project.get('platform', 'the platform')
    industry = project.get('industry', 'your industry')
    requirements = project.get('requirements', '')
    highlight_name = highlight.get('name', 'relevant project') if highlight else "Huawei projects"
    highlight_result = highlight.get('result_en', 'impressive results') if highlight else "impressive results"

    # Detect work type
    work_type = detect_work_type(project)

    # Customize based on tone
    if "professional and formal" in tone:
        opening = f"I came across your {title} posting on {platform} and was impressed by the focus on enterprise-grade design solutions."
        value_prop = f"My experience leading {highlight_name} at Huawei—achieving {highlight_result}—has given me deep expertise in building scalable, user-centric interfaces for complex systems. Your requirements for {industry} align closely with my background."
        cta = "I would welcome the opportunity to discuss how my experience could contribute to your team's success."
    elif "friendly" in tone:
        opening = f"I saw your {title} posting on {platform} and loved what you're building in the {industry} space!"
        value_prop = f"At Huawei, I led {highlight_name}, which achieved {highlight_result}. I've since helped many {industry} companies scale their design without the overhead of full-time hires."
        cta = "Would love to chat about your vision!"
    else:
        opening = f"I noticed your {title} posting on {platform} and the focus on {industry} caught my attention."
        value_prop = f"During my 6 years at Huawei, I led {highlight_name}, delivering {highlight_result}. This experience translates directly to your needs for thoughtful, effective design."
        cta = "Let's connect!"

    # Generate subject lines
    subject_lines = generate_subject_lines(project, highlight)

    # Build email body with work type awareness
    email_parts = []

    # Opening
    email_parts.append(f"Hi {client},\n")
    email_parts.append(opening)
    email_parts.append(value_prop)

    # Add timezone/remote work info
    email_parts.append(f"\nI'm a remote-based Senior UX Designer located in China (UTC+8), with extensive experience collaborating internationally.")
    email_parts.append(f"My portfolio: https://hueshadow.com")

    # Add communication preference for part-time/project work
    if work_type["needs_communication_note"]:
        comm_note = get_communication_note(work_type)
        email_parts.append(comm_note)
    else:
        email_parts.append("\nI'm available for asynchronous collaboration and happy to discuss via email.")

    # CTA
    email_parts.append(f"\n{cta}")
    email_parts.append(f"\nBest regards,")
    email_parts.append(f"Rong Huang (黄蓉)")
    email_parts.append(f"Senior UX Designer | Product Manager")
    email_parts.append(f"Portfolio: https://hueshadow.com")
    email_parts.append(f"LinkedIn: {USER_PROFILE['linkedin']}")
    email_parts.append(f"Timezone: {USER_PROFILE['timezone']}")

    email_body = "\n".join(email_parts)

    return subject_lines, email_body


def save_email_file(project: Dict, subject_lines: List[str], email_body: str,
                    output_dir: Path, highlight: Dict, work_type: Dict = None):
    """Save the generated email as a markdown file"""
    client = project.get('client', 'Unknown')
    priority_score = project.get('priority_score', 0)
    match_score = project.get('match_score', 0)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_client_name = re.sub(r'[^a-zA-Z0-9]', '', client)[:15]
    project_num = project.get('id', 1)
    filename = f"project_{project_num:03d}_{safe_client_name}_email.md"
    filepath = output_dir / filename

    # Create markdown content
    highlight_name = highlight.get('name', 'N/A') if highlight else "N/A"
    highlight_result = highlight.get('result_en', 'N/A') if highlight else "N/A"

    # Get work type info
    if work_type is None:
        work_type = detect_work_type(project)

    work_type_info = f"""
## Work Type & Communication Preferences

- **Work Type Detected:** {work_type['work_type_label']}
- **Remote Available:** {'Yes' if work_type['is_remote'] else 'No'}
- **Communication Preference:** Email-based asynchronous
- **Timezone:** {USER_PROFILE['timezone']} (China/Singapore)
- **Phone Calls:** Not available (email preferred)

---
"""

    content = f"""# AI-Generated Marketing Email - {client}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Priority Score:** {priority_score}/100
**Match Score:** {match_score}/100
**Recommended Highlight:** {highlight_name} ({highlight_result})

---

## Project Details

### Basic Information
- **Role:** {project.get('title', 'N/A')}
- **Company:** {client}
- **Industry:** {project.get('industry', 'N/A')}
- **Platform:** {project.get('platform', 'N/A')}
- **Budget:** {project.get('budget_range', 'N/A')}
- **Client Type:** {project.get('client_type', 'N/A')}

### Work Scope
- **Work Type:** {project.get('work_scope', 'N/A')}
- **Deliverables:** {project.get('deliverables', 'N/A')}
- **Format:** {project.get('format', 'N/A')}
- **Timeline:** {project.get('timeline', 'N/A')}

### Full Requirements
{project.get('requirements', 'N/A')}

### Match Reasons
{chr(10).join(f'- {r}' for r in project.get('match_reasons', []))}

---

## Contact Information

- **Email:** {project.get('email', 'Via platform')}
- **LinkedIn:** {project.get('linkedin', 'N/A')}
- **Website:** {project.get('website', 'N/A')}
- **Platform Link:** {project.get('platform_link', '#')}

---

{work_type_info}

## Subject Lines (Alternatives)

1. {subject_lines[0] if len(subject_lines) > 0 else 'N/A'}
2. {subject_lines[1] if len(subject_lines) > 1 else 'N/A'}
3. {subject_lines[2] if len(subject_lines) > 2 else 'N/A'}

---

## Email Body

{email_body}

---

## Notes

- [ ] Personalize opening if you know the hiring manager's name
- [ ] Verify all links work before sending
- [ ] Consider local time for sending
- [ ] Track in your CRM

---

*Generated by AI Email Generator for Design Job Finder*
*User Profile: {USER_PROFILE['name']} - {USER_PROFILE['role']}*
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def find_latest_json() -> Optional[Path]:
    """Find the most recent projects JSON file"""
    if LATEST_DIR.exists():
        json_files = list(LATEST_DIR.glob("projects_for_ai_emails_*.json"))
        if json_files:
            return sorted(json_files)[-1]  # Most recent

    # Fallback: search all date folders
    for date_dir in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if date_dir.is_dir() and date_dir.name.match(r'\d{4}-\d{2}-\d{2}'):
            json_files = list(date_dir.glob("projects_for_ai_emails_*.json"))
            if json_files:
                return sorted(json_files)[-1]

    return None


def main():
    print("=" * 70)
    print("AI Email Generator - Design Job Finder")
    print("=" * 70)

    # Find latest JSON file
    json_path = find_latest_json()
    if not json_path:
        print("❌ Error: No projects JSON file found!")
        print("   Run 'python3 process_design_projects.py' first.")
        return

    print(f"\n📁 Input: {json_path}")
    print(f"📁 Output: {AI_EMAILS_DIR}")

    # Load projects
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    user_summary = data.get('user_profile', {})

    print(f"\n📊 Total projects in JSON: {len(projects)}")

    # Filter high-match projects (match_score >= 50)
    high_match_projects = [p for p in projects if p.get('match_score', 0) >= 50]

    print(f"🎯 High-match projects (score >= 50): {len(high_match_projects)}")

    if not high_match_projects:
        print("❌ No high-match projects found!")
        return

    # Ensure output directory exists
    AI_EMAILS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate emails for each project
    stats = {
        'total': len(high_match_projects),
        'generated': 0,
        'failed': 0
    }

    print(f"\n{'='*70}")
    print("Generating personalized emails...")
    print(f"{'='*70}\n")

    for i, project in enumerate(high_match_projects, 1):
        client = project.get('client', 'Unknown')
        title = project.get('title', 'N/A')[:40]
        match_score = project.get('match_score', 0)
        priority_score = project.get('priority_score', 0)

        print(f"[{i:2d}/{stats['total']}] {client}")
        print(f"      Role: {title}...")
        print(f"      Match: {match_score}/100 | Priority: {priority_score}/100")

        # Detect work type
        work_type = detect_work_type(project)
        if work_type['needs_communication_note']:
            print(f"      Work Type: {work_type['work_type_label']} 📧 Email-only")
        else:
            print(f"      Work Type: {work_type['work_type_label']}")

        # Select appropriate highlight
        highlight = select_highlight_for_project(project)
        if highlight:
            print(f"      Highlight: {highlight.get('name', 'N/A')}")

        # Try to generate with Claude, fallback to template
        subject_lines, email_body = generate_email_with_claude(
            create_email_prompt(project, highlight)
        )

        if not email_body:
            print("      Using template-based generation...")
            subject_lines, email_body = generate_template_email(project, highlight)

        # Save the email
        try:
            filepath = save_email_file(project, subject_lines, email_body,
                                       AI_EMAILS_DIR, highlight, work_type)
            print(f"      ✅ Saved: {filepath.name}")
            stats['generated'] += 1
        except Exception as e:
            print(f"      ❌ Failed to save: {e}")
            stats['failed'] += 1

        print()

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"High-match projects processed: {stats['total']}")
    print(f"Emails successfully generated: {stats['generated']}")
    print(f"Failed: {stats['failed']}")
    print(f"\n📁 Output directory: {AI_EMAILS_DIR}")
    print(f"📧 Next step: Review emails in {AI_EMAILS_DIR}")
    print(f"\n🌐 Remote-first approach | 📧 Email communication | ⏰ UTC+8 Timezone")
    print(f"{'='*70}\n")

    return stats


if __name__ == "__main__":
    main()
