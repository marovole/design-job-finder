#!/usr/bin/env python3
"""
Exa Parser - PM Job Finder
Parses Exa deep researcher results into structured job data.
"""

import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def get_anthropic_client() -> Optional[object]:
    """Get Anthropic client if available and API key is set."""
    if not ANTHROPIC_AVAILABLE:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    return Anthropic(api_key=api_key)


def parse_exa_research_result(
    raw_result: str,
    platform: str = "Unknown",
    use_llm: bool = True
) -> List[Dict]:
    """
    Parse Exa deep researcher result into structured job data.

    Args:
        raw_result: Raw text/JSON from Exa deep researcher
        platform: Source platform name
        use_llm: Whether to use LLM for parsing

    Returns:
        List of structured job dictionaries
    """
    if not raw_result or not raw_result.strip():
        return []

    # Try JSON parsing first
    try:
        data = json.loads(raw_result)
        if isinstance(data, list):
            return [_normalize_job(job, platform) for job in data]
        elif isinstance(data, dict) and 'jobs' in data:
            return [_normalize_job(job, platform) for job in data['jobs']]
    except json.JSONDecodeError:
        pass

    # Use LLM to extract structured data
    if use_llm:
        client = get_anthropic_client()
        if client:
            return _llm_parse_research_result(raw_result, platform, client)

    # Fallback: basic text extraction
    return _basic_text_extraction(raw_result, platform)


def _llm_parse_research_result(
    raw_result: str,
    platform: str,
    client: object
) -> List[Dict]:
    """Use Claude to parse research result into structured data."""

    prompt = f"""从以下研究报告中提取职位数据。

## 研究报告内容
{raw_result[:15000]}  # Limit to avoid token overflow

## 输出要求
输出 JSON 数组，每个职位包含以下字段：

```json
[
  {{
    "job_title": "职位名称",
    "company_name": "公司名称",
    "job_description": "职位描述 (100-200字)",
    "responsibilities": ["职责1", "职责2"],
    "requirements": ["要求1", "要求2"],
    "skills_required": ["技能1", "技能2"],
    "job_level": "Entry/Mid/Senior/Lead/Director/VP",
    "job_type": "Full-time/Contract/Freelance",
    "remote_policy": "Full Remote/Hybrid/On-site",
    "salary_min_usd": 数字或null,
    "salary_max_usd": 数字或null,
    "salary_range": "原始薪资文本",
    "equity_offered": true/false,
    "company_stage": "Seed/Series A/B/C/D+/Growth/Public",
    "funding_round": "融资轮次",
    "funding_amount": "融资金额",
    "company_size": "公司规模",
    "company_industry": "行业",
    "product_type": "ToB SaaS/ToC Consumer/等",
    "location": "工作地点",
    "timezone_requirements": "时区要求",
    "visa_sponsorship": true/false,
    "application_url": "申请链接",
    "posted_date": "YYYY-MM-DD 或 null",
    "recruiter_email": "邮箱或null",
    "recruiter_linkedin": "LinkedIn链接或null"
  }}
]
```

## 解析规则
1. 如果薪资不确定，根据职位级别和行业估算美元年薪：
   - Entry/Junior: $80,000-$120,000
   - Mid: $100,000-$150,000
   - Senior: $150,000-$220,000
   - Lead/Principal: $180,000-$280,000
   - Director: $200,000-$350,000
   - VP: $250,000-$400,000

2. 识别 AI/ML 相关关键词，准确标记 company_industry

3. 如果发布日期不确定，设为 null

只输出 JSON 数组，不要其他文字。"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text.strip()

        # Extract JSON from response
        if result_text.startswith("```"):
            # Remove markdown code blocks
            lines = result_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```json"):
                    in_json = True
                    continue
                elif line.startswith("```"):
                    in_json = False
                    continue
                if in_json:
                    json_lines.append(line)
            result_text = "\n".join(json_lines)

        jobs = json.loads(result_text)

        return [_normalize_job(job, platform) for job in jobs]

    except Exception as e:
        print(f"Warning: LLM parsing failed: {e}")
        return _basic_text_extraction(raw_result, platform)


def _basic_text_extraction(raw_result: str, platform: str) -> List[Dict]:
    """Basic text extraction without LLM (very limited)."""
    jobs = []

    # Look for job title patterns
    title_patterns = [
        r"(Senior|Lead|Principal|Staff|Head of|Director|VP|Chief)?\s*(Product Manager|PM|产品经理|产品总监)",
        r"(Product Manager|PM)\s*[-–]\s*([A-Za-z\s]+)",
    ]

    lines = raw_result.split("\n")
    current_job = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for company names (often followed by job titles)
        for pattern in title_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                if current_job:
                    jobs.append(current_job)

                current_job = {
                    "job_title": match.group(0),
                    "company_name": "Unknown",
                    "job_description": "",
                    "responsibilities": [],
                    "requirements": [],
                    "skills_required": [],
                    "job_level": _infer_level(match.group(0)),
                    "job_type": "Full-time",
                    "remote_policy": "Unknown",
                    "salary_min_usd": None,
                    "salary_max_usd": None,
                    "source_platform": platform,
                }
                break

    if current_job:
        jobs.append(current_job)

    return [_normalize_job(job, platform) for job in jobs]


def _infer_level(title: str) -> str:
    """Infer job level from title."""
    title_lower = title.lower()
    if "vp" in title_lower or "chief" in title_lower:
        return "VP"
    elif "director" in title_lower or "head of" in title_lower:
        return "Director"
    elif "lead" in title_lower or "principal" in title_lower:
        return "Lead"
    elif "senior" in title_lower or "staff" in title_lower:
        return "Senior"
    elif "junior" in title_lower or "entry" in title_lower:
        return "Entry"
    else:
        return "Mid"


def _normalize_job(job: Dict, platform: str) -> Dict:
    """Normalize job data to ensure all required fields exist."""
    today = datetime.now().strftime('%Y-%m-%d')

    normalized = {
        "job_title": job.get("job_title", "Product Manager"),
        "company_name": job.get("company_name", "Unknown"),
        "job_description": job.get("job_description", ""),
        "responsibilities": job.get("responsibilities", []),
        "requirements": job.get("requirements", []),
        "skills_required": job.get("skills_required", []),
        "job_level": job.get("job_level", "Senior"),
        "job_type": job.get("job_type", "Full-time"),
        "remote_policy": job.get("remote_policy", "Unknown"),
        "salary_range": job.get("salary_range", ""),
        "salary_min_usd": job.get("salary_min_usd"),
        "salary_max_usd": job.get("salary_max_usd"),
        "equity_offered": job.get("equity_offered", False),
        "company_stage": job.get("company_stage", "Unknown"),
        "funding_round": job.get("funding_round", ""),
        "funding_amount": job.get("funding_amount", ""),
        "company_size": job.get("company_size", ""),
        "company_industry": job.get("company_industry", ""),
        "product_type": job.get("product_type", ""),
        "location": job.get("location", ""),
        "timezone_requirements": job.get("timezone_requirements", ""),
        "visa_sponsorship": job.get("visa_sponsorship", False),
        "application_url": job.get("application_url", ""),
        "posted_date": job.get("posted_date") or today,
        "recruiter_email": job.get("recruiter_email"),
        "recruiter_linkedin": job.get("recruiter_linkedin"),
        "source_platform": platform,
        "data_collection_date": today,
    }

    # Ensure lists are actually lists
    for field in ["responsibilities", "requirements", "skills_required"]:
        if isinstance(normalized[field], str):
            normalized[field] = [normalized[field]] if normalized[field] else []

    return normalized


def parse_multiple_results(
    results: Dict[str, str],
    use_llm: bool = True
) -> Dict[str, List[Dict]]:
    """
    Parse multiple Exa research results from different platforms.

    Args:
        results: Dictionary of {platform: raw_result}
        use_llm: Whether to use LLM for parsing

    Returns:
        Dictionary of {platform: [parsed_jobs]}
    """
    parsed = {}

    for platform, raw_result in results.items():
        print(f"  Parsing results from {platform}...")
        jobs = parse_exa_research_result(raw_result, platform, use_llm)
        parsed[platform] = jobs
        print(f"    Found {len(jobs)} jobs")

    return parsed


if __name__ == "__main__":
    # Test the parser
    print("=" * 60)
    print("Exa Parser Test")
    print("=" * 60)

    # Sample research result for testing
    sample_result = """
    Based on my research, here are some Product Manager positions:

    1. **Senior Product Manager - AI Platform** at Anthropic
       - Location: San Francisco, CA (Hybrid)
       - Salary: $200,000 - $300,000/year
       - Requirements: 5+ years PM experience, AI/ML background
       - They're working on Claude and AI safety

    2. **Founding PM** at Resend (YC W23)
       - Location: Remote (Global)
       - Salary: $150,000 - $200,000 + equity
       - Series A, $18M raised
       - Building developer email infrastructure

    3. **Head of Product** at Linear
       - Location: Remote
       - Salary: $250,000 - $350,000 + significant equity
       - Series B, looking for experienced product leaders
    """

    jobs = parse_exa_research_result(sample_result, "Test Platform", use_llm=False)

    print(f"\nParsed {len(jobs)} jobs (without LLM):")
    for job in jobs:
        print(f"  - {job['job_title']} @ {job['company_name']}")

    # Test with LLM if available
    client = get_anthropic_client()
    if client:
        print("\n--- Testing with LLM parsing ---")
        jobs_llm = parse_exa_research_result(sample_result, "Test Platform", use_llm=True)
        print(f"Parsed {len(jobs_llm)} jobs (with LLM):")
        for job in jobs_llm:
            print(f"  - {job['job_title']} @ {job['company_name']}")
            print(f"    Level: {job['job_level']}, Remote: {job['remote_policy']}")
            print(f"    Salary: ${job.get('salary_min_usd', '?')} - ${job.get('salary_max_usd', '?')}")
    else:
        print("\n⚠️ Claude API not available for LLM parsing test")

    print("\n" + "=" * 60)
