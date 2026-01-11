#!/usr/bin/env python3
"""
PM Job Finder - Data Processing & Match Analysis Generator
Processes PM job data, calculates match scores, and generates application support materials.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from user_profile import (
    get_user_profile,
    get_experience_level_ranges,
    has_ai_agent_relevance,
    get_ai_relevance_bonus_max,
)

try:
    from semantic_matcher import calculate_semantic_skill_match

    SEMANTIC_MATCHER_AVAILABLE = True
except ImportError:
    SEMANTIC_MATCHER_AVAILABLE = False

try:
    from company_analyzer import run_company_analysis, CompanyAnalysisResult

    COMPANY_ANALYZER_AVAILABLE = True
except ImportError:
    COMPANY_ANALYZER_AVAILABLE = False

# Output directory structure for daily runs
OUTPUT_DIR = Path("output")
TODAY = datetime.now().strftime("%Y-%m-%d")
DATE_DIR = OUTPUT_DIR / TODAY


# Create date-based directories
def setup_output_directories():
    """Create output directory structure"""
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        DATE_DIR.mkdir(exist_ok=True)
        (DATE_DIR / "match_analysis").mkdir(exist_ok=True)
        (DATE_DIR / "match_analysis" / "high_match").mkdir(parents=True, exist_ok=True)
        (DATE_DIR / "match_analysis" / "good_match").mkdir(parents=True, exist_ok=True)
        (DATE_DIR / "application_materials").mkdir(exist_ok=True)
        (DATE_DIR / "application_materials" / "cover_letters").mkdir(
            parents=True, exist_ok=True
        )
        (DATE_DIR / "company_research").mkdir(exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directories: {e}")


def update_latest_symlink():
    """Create or update the 'latest' symlink to point to today's folder"""
    latest_link = OUTPUT_DIR / "latest"
    try:
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
        os.symlink(str(DATE_DIR.resolve()), str(latest_link))
    except OSError as e:
        print(f"      Note: Symlink not supported ({e})")


# =============================================================================
# SAMPLE PM JOB DATA - Minimal test data, real data comes from exa_parser
# =============================================================================
# NOTE: This is sample data for testing. In production, use exa_parser.py
# to parse real data from Exa deep researcher.
pm_jobs_data = {
    # Sample AI-focused job for testing AI relevance bonus
    "Sample - AI Jobs": [
        {
            "job_title": "Senior Product Manager - AI Agents",
            "company_name": "Anthropic",
            "job_description": "Shape the future of AI assistants. Work on Claude and define how AI helps humans be more productive. Lead AI agent product strategy.",
            "responsibilities": [
                "Define AI agent features",
                "Work with research team",
                "Shape product vision",
                "Drive user research",
            ],
            "requirements": [
                "5+ years PM experience",
                "AI/ML product experience",
                "LLM understanding",
                "Strong writing skills",
            ],
            "skills_required": [
                "AI/ML",
                "LLM",
                "AI Agent",
                "Product Strategy",
                "User Research",
            ],
            "job_level": "Senior",
            "job_type": "Full-time",
            "remote_policy": "Full Remote",
            "salary_range": "$200,000 - $300,000/year",
            "salary_min_usd": 200000,
            "salary_max_usd": 300000,
            "equity_offered": True,
            "company_stage": "Series D+",
            "funding_round": "Series D",
            "funding_amount": "$4B",
            "company_size": "500-1000",
            "company_industry": "AI/ML",
            "product_type": "ToB SaaS",
            "location": "Remote (Global)",
            "timezone_requirements": "Flexible",
            "visa_sponsorship": True,
            "application_url": "https://anthropic.com/careers",
            "posted_date": "2026-01-07",
            "recruiter_email": "jobs@anthropic.com",
            "recruiter_linkedin": None,
        },
    ],
    # Sample Developer Tools job
    "Sample - Dev Tools": [
        {
            "job_title": "Founding Product Manager",
            "company_name": "Resend",
            "job_description": "Join as the first PM at a fast-growing developer email infrastructure company. Shape product strategy from the ground up.",
            "responsibilities": [
                "Define product vision",
                "Work directly with founders",
                "Ship features weekly",
                "Talk to customers daily",
            ],
            "requirements": [
                "5+ years PM experience",
                "Developer tools or API experience",
                "Startup experience",
                "Technical background preferred",
            ],
            "skills_required": [
                "Developer Tools",
                "API Products",
                "Startup",
                "Technical PM",
            ],
            "job_level": "Senior",
            "job_type": "Full-time",
            "remote_policy": "Full Remote",
            "salary_range": "$150,000 - $200,000/year + 0.5-1% equity",
            "salary_min_usd": 150000,
            "salary_max_usd": 200000,
            "equity_offered": True,
            "company_stage": "Series A",
            "funding_round": "Series A",
            "funding_amount": "$18M",
            "company_size": "20-50",
            "company_industry": "Developer Tools",
            "product_type": "ToB SaaS",
            "location": "Remote (Global)",
            "timezone_requirements": "Americas preferred",
            "visa_sponsorship": False,
            "application_url": "https://resend.com/careers",
            "posted_date": "2026-01-08",
            "recruiter_email": "careers@resend.com",
            "recruiter_linkedin": None,
        },
    ],
    # Sample non-AI job for comparison
    "Sample - E-commerce": [
        {
            "job_title": "Senior PM - Marketplace",
            "company_name": "Faire",
            "job_description": "Build the future of wholesale commerce. Own the retailer experience and drive GMV growth.",
            "responsibilities": [
                "Own retailer experience",
                "Drive marketplace growth",
                "Define feature roadmap",
                "Work with data team",
            ],
            "requirements": [
                "5+ years PM experience",
                "Marketplace experience",
                "E-commerce background",
                "Data-driven",
            ],
            "skills_required": ["Marketplace", "E-commerce", "Growth", "Data Analysis"],
            "job_level": "Senior",
            "job_type": "Full-time",
            "remote_policy": "Full Remote",
            "salary_range": "$160,000 - $220,000/year",
            "salary_min_usd": 160000,
            "salary_max_usd": 220000,
            "equity_offered": True,
            "company_stage": "Series G",
            "funding_round": "Series G",
            "funding_amount": "$400M",
            "company_size": "1000-2000",
            "company_industry": "E-commerce/Marketplace",
            "product_type": "ToB SaaS",
            "location": "Remote (US/Canada)",
            "timezone_requirements": "North America",
            "visa_sponsorship": False,
            "application_url": "https://faire.com/careers",
            "posted_date": "2026-01-04",
            "recruiter_email": "talent@faire.com",
            "recruiter_linkedin": None,
        },
    ],
}


# =============================================================================
# MATCH SCORING ALGORITHM
# =============================================================================


def calculate_match_score(job, user_profile):
    """
    Calculate job match score 0-100 based on user profile.

    Weight Distribution:
    - Experience Level Match: 25 points
    - Industry/Product Type Match: 20 points
    - Remote Policy Match: 20 points
    - Company Stage Match: 15 points
    - Salary Competitiveness: 10 points
    - Skills Match: 10 points

    Returns: (score, breakdown_dict, highlights, concerns)
    """
    score = 0
    breakdown = {}
    highlights = []
    concerns = []

    # === 1. Experience Level Match (25 points) ===
    job_level = job.get("job_level", "Mid")
    user_years = user_profile.get("years_experience", 8)
    level_ranges = get_experience_level_ranges()

    min_years, max_years = level_ranges.get(job_level, (5, 10))

    if min_years <= user_years <= max_years:
        breakdown["experience_match"] = 25
        highlights.append(f"{user_years}年经验完美匹配{job_level}级别")
    elif user_years > max_years:
        breakdown["experience_match"] = 18
        concerns.append(f"可能资历过高 ({user_years}年 vs {job_level}级别)")
    elif user_years >= min_years - 2:
        breakdown["experience_match"] = 15
        highlights.append("经验基本匹配")
    else:
        breakdown["experience_match"] = 5
        concerns.append("经验年限不足")

    score += breakdown["experience_match"]

    # === 2. Industry/Product Type Match (20 points) ===
    job_industry = job.get("company_industry", "").lower()
    product_type = job.get("product_type", "").lower()

    industry_score = 0
    for pref_industry, weight in user_profile.get("preferred_industries", {}).items():
        if (
            pref_industry.lower() in job_industry
            or pref_industry.lower() in product_type
        ):
            industry_score = max(industry_score, int(20 * weight))
            if weight >= 0.9:
                highlights.append(f"行业匹配: {pref_industry}")
            break

    if industry_score == 0:
        industry_score = 6
        concerns.append(f"非首选行业: {job.get('company_industry', 'Unknown')}")

    breakdown["industry_match"] = industry_score
    score += industry_score

    # === 3. Remote Policy Match (20 points) ===
    remote_policy = job.get("remote_policy", "On-site")
    location_prefs = user_profile.get("location_preferences", {})

    remote_score = 0
    for policy, weight in location_prefs.items():
        if policy.lower() in remote_policy.lower():
            remote_score = int(20 * weight)
            if weight >= 0.8:
                highlights.append(f"远程政策匹配: {remote_policy}")
            break

    if remote_score == 0:
        remote_score = 4
        concerns.append(f"远程政策: {remote_policy}")

    breakdown["remote_match"] = remote_score
    score += remote_score

    # === 4. Company Stage Match (15 points) ===
    company_stage = job.get("company_stage", "Unknown")
    stage_prefs = user_profile.get("preferred_company_stages", {})

    stage_score = 0
    for stage, weight in stage_prefs.items():
        if stage.lower() in company_stage.lower():
            stage_score = int(15 * weight)
            if weight >= 0.9:
                highlights.append(f"公司阶段匹配: {company_stage}")
            break

    if stage_score == 0:
        stage_score = 5

    breakdown["company_stage_match"] = stage_score
    score += stage_score

    # === 5. Salary Competitiveness (10 points) ===
    salary_mid = (job.get("salary_min_usd", 0) + job.get("salary_max_usd", 0)) / 2
    salary_target = user_profile.get("salary_expectation_target", 200000)
    salary_min = user_profile.get("salary_expectation_min", 150000)

    if salary_mid >= salary_target:
        breakdown["salary_match"] = 10
        highlights.append(f"薪资超过期望: ${salary_mid:,.0f}")
    elif salary_mid >= salary_min:
        breakdown["salary_match"] = 7
        highlights.append(f"薪资达到最低要求: ${salary_mid:,.0f}")
    elif salary_mid >= salary_min * 0.8:
        breakdown["salary_match"] = 4
        concerns.append(f"薪资略低于期望: ${salary_mid:,.0f}")
    else:
        breakdown["salary_match"] = 2
        concerns.append(f"薪资较低: ${salary_mid:,.0f}")

    score += breakdown["salary_match"]

    # === 6. Skills Match (10 points base, uses semantic matching if available) ===
    required_skills = job.get("skills_required", [])
    requirements = job.get("requirements", [])

    if SEMANTIC_MATCHER_AVAILABLE and required_skills:
        # Use semantic matching with LLM
        try:
            skill_score, matched_skills, skill_gaps = calculate_semantic_skill_match(
                requirements, required_skills, user_profile, use_llm=True
            )
            breakdown["skills_match"] = int(10 * skill_score)
            if skill_score >= 0.7:
                highlights.append(f"技能语义匹配度高: {len(matched_skills)}项匹配")
            job["_semantic_matched_skills"] = matched_skills
            job["_semantic_skill_gaps"] = skill_gaps
        except Exception:
            # Fallback to keyword matching
            breakdown["skills_match"] = _keyword_skill_match(
                required_skills, user_profile
            )
    elif required_skills:
        # Keyword matching fallback
        breakdown["skills_match"] = _keyword_skill_match(required_skills, user_profile)
        required_skills_lower = set(s.lower() for s in required_skills)
        user_skills = set(
            s.lower()
            for s in user_profile.get("core_skills", [])
            + user_profile.get("technical_skills", [])
        )
        overlap = len(required_skills_lower & user_skills)
        if overlap / len(required_skills_lower) >= 0.7:
            highlights.append(f"技能匹配度高: {overlap}/{len(required_skills_lower)}")
    else:
        breakdown["skills_match"] = 5

    score += breakdown["skills_match"]

    # === 7. AI Agent Relevance Bonus (up to 15 extra points) ===
    is_ai_relevant, ai_relevance = has_ai_agent_relevance(job)
    ai_bonus_max = get_ai_relevance_bonus_max()

    if is_ai_relevant:
        ai_bonus = int(ai_bonus_max * ai_relevance)
        breakdown["ai_relevance_bonus"] = ai_bonus
        score += ai_bonus
        if ai_relevance >= 0.6:
            highlights.append(
                f"🤖 AI Agent 相关职位 (匹配度 {ai_relevance * 100:.0f}%)"
            )
        elif ai_relevance >= 0.3:
            highlights.append(f"AI 相关职位")
    else:
        breakdown["ai_relevance_bonus"] = 0

    # Max score is now 115 (100 base + 15 AI bonus), normalize for A+ tier
    return score, breakdown, highlights, concerns


def _keyword_skill_match(required_skills: list, user_profile: dict) -> int:
    """Fallback keyword-based skill matching."""
    required_skills_lower = set(s.lower() for s in required_skills)
    user_skills = set(
        s.lower()
        for s in user_profile.get("core_skills", [])
        + user_profile.get("technical_skills", [])
        + user_profile.get("ai_agent_skills", [])
    )

    if not required_skills_lower:
        return 5

    overlap = len(required_skills_lower & user_skills)
    skill_ratio = overlap / len(required_skills_lower)
    return int(10 * skill_ratio)


def determine_match_label(score):
    """Convert score to match label. Supports A+ tier for AI-relevant jobs (score > 100)."""
    if score >= 100:
        return "A+级-极高匹配(AI)"
    elif score >= 80:
        return "A级-极高匹配"
    elif score >= 60:
        return "B级-高匹配"
    elif score >= 40:
        return "C级-中匹配"
    else:
        return "D级-低匹配"


# =============================================================================
# APPLICATION SUPPORT GENERATION
# =============================================================================


def generate_resume_suggestions(job):
    """Generate resume focus suggestions for a specific job"""
    suggestions = []

    # Based on job level
    level = job.get("job_level", "Senior")
    if level in ["Lead", "Director", "VP"]:
        suggestions.append("突出团队管理和领导力经验")
        suggestions.append("强调战略规划和商业影响")
    else:
        suggestions.append("展示独立负责产品线的经验")
        suggestions.append("量化产品指标成果 (用户增长、收入、留存等)")

    # Based on industry
    industry = job.get("company_industry", "")
    if "AI" in industry or "ML" in industry:
        suggestions.append("突出AI/ML产品经验和技术理解")
    if "SaaS" in industry or "ToB" in job.get("product_type", ""):
        suggestions.append("强调B2B产品经验和企业客户管理")
    if "Developer" in industry:
        suggestions.append("展示技术背景和开发者生态理解")

    # Based on company stage
    stage = job.get("company_stage", "")
    if stage in ["Seed", "Series A", "Series B"]:
        suggestions.append("突出从0到1的产品经验")
        suggestions.append("强调快速迭代和创业心态")
    elif stage in ["Public", "Enterprise"]:
        suggestions.append("强调大规模产品运营经验")
        suggestions.append("展示跨部门协作能力")

    return suggestions


def generate_cover_letter_points(job):
    """Generate cover letter talking points for a specific job"""
    points = []

    company = job.get("company_name", "")
    title = job.get("job_title", "")

    points.append(f"开篇: 表达对{company}产品的真实热情和了解")

    # Based on product type
    product_type = job.get("product_type", "")
    if "ToB" in product_type:
        points.append("中段: 分享B2B产品经验，特别是企业客户需求理解")
    elif "ToC" in product_type:
        points.append("中段: 展示消费者产品直觉和用户增长经验")

    # Based on company stage
    stage = job.get("company_stage", "")
    if stage in ["Seed", "Series A", "Series B"]:
        points.append("强调: 创业环境适应能力，快速学习和执行")
    else:
        points.append("强调: 在复杂组织中推动变革的能力")

    points.append(f"结尾: 明确表达对{title}职位的兴趣和贡献愿景")

    return points


def generate_interview_prep(job):
    """Generate interview preparation notes"""
    prep_notes = []

    company = job.get("company_name", "")
    industry = job.get("company_industry", "")

    prep_notes.append(f"研究{company}的产品线和最新动态")
    prep_notes.append(f"准备{industry}行业趋势的见解")
    prep_notes.append("准备2-3个你主导的产品案例，包含具体数据")
    prep_notes.append("思考对该职位的前90天计划")

    # Based on job level
    level = job.get("job_level", "")
    if level in ["Lead", "Director", "VP"]:
        prep_notes.append("准备团队管理和人才发展的经验分享")
        prep_notes.append("准备产品战略和愿景类问题")

    # Based on skills
    skills = job.get("skills_required", [])
    if "AI" in str(skills) or "ML" in str(skills):
        prep_notes.append("准备AI产品伦理和负责任AI的观点")

    return prep_notes


# =============================================================================
# DATA PROCESSING
# =============================================================================


def normalize_company_name(name: str) -> str:
    """Normalize company name for deduplication."""
    name = name.lower().strip()
    # Remove common suffixes
    for suffix in [
        " inc",
        " inc.",
        " llc",
        " ltd",
        " limited",
        " corp",
        " corporation",
        " ug",
        " gmbh",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()


def normalize_job_key(job: dict) -> str:
    """Generate unique key for job deduplication."""
    company = normalize_company_name(job.get("company_name", ""))
    title = job.get("job_title", "").lower()

    # Remove level words to match similar positions
    for level in [
        "senior ",
        "lead ",
        "principal ",
        "staff ",
        "head of ",
        "director of ",
        "vp of ",
    ]:
        title = title.replace(level, "")

    # Extract first 3 meaningful words
    words = [w for w in title.split() if len(w) > 2][:3]
    title_key = "_".join(words)

    return f"{company}_{title_key}"


def calculate_job_completeness(job: dict) -> int:
    """Calculate information completeness score for a job."""
    score = 0
    if job.get("salary_min_usd"):
        score += 3
    if job.get("recruiter_email"):
        score += 3
    if job.get("recruiter_linkedin"):
        score += 2
    if len(job.get("skills_required", [])) > 3:
        score += 2
    if len(job.get("job_description", "")) > 200:
        score += 1
    if job.get("equity_offered"):
        score += 1
    if job.get("funding_amount"):
        score += 1
    return score


def deduplicate_jobs(jobs: list) -> list:
    """
    Deduplicate jobs across platforms, keeping the most complete version.

    Args:
        jobs: List of job dictionaries

    Returns:
        Deduplicated list of jobs
    """
    seen = {}

    for job in jobs:
        key = normalize_job_key(job)

        if key not in seen:
            seen[key] = job
        else:
            # Keep the more complete version
            existing_score = calculate_job_completeness(seen[key])
            new_score = calculate_job_completeness(job)

            if new_score > existing_score:
                # Keep new job but merge source platforms
                old_platform = seen[key].get("source_platform", "")
                new_platform = job.get("source_platform", "")
                if old_platform and old_platform != new_platform:
                    job["source_platforms"] = f"{new_platform}, {old_platform}"
                seen[key] = job

    return list(seen.values())


def process_jobs(jobs_data: dict = None):
    """
    Process all job data and generate match analysis.

    Args:
        jobs_data: Dictionary of {platform: [jobs]} or None to use sample data

    Returns:
        List of processed jobs sorted by match score
    """
    user_profile = get_user_profile()
    all_jobs = []

    # Use provided data or fallback to sample data
    data_source = jobs_data if jobs_data is not None else pm_jobs_data

    # Flatten all jobs from all platforms
    for platform, jobs in data_source.items():
        for job in jobs:
            job["source_platform"] = platform
            job["data_collection_date"] = TODAY

            # Calculate match score
            score, breakdown, highlights, concerns = calculate_match_score(
                job, user_profile
            )
            job["match_score"] = score
            job["match_label"] = determine_match_label(score)
            job["match_breakdown"] = breakdown
            job["match_highlights"] = highlights
            job["match_concerns"] = concerns

            # Generate application support
            job["resume_suggestions"] = generate_resume_suggestions(job)
            job["cover_letter_points"] = generate_cover_letter_points(job)
            job["interview_prep"] = generate_interview_prep(job)

            # Calculate days since posted
            try:
                posted = datetime.strptime(job.get("posted_date", TODAY), "%Y-%m-%d")
                job["days_since_posted"] = (datetime.now() - posted).days
            except Exception:
                job["days_since_posted"] = 0

            all_jobs.append(job)

    # Deduplicate jobs across platforms
    original_count = len(all_jobs)
    all_jobs = deduplicate_jobs(all_jobs)
    dedup_count = original_count - len(all_jobs)
    if dedup_count > 0:
        print(
            f"      Deduplicated: {original_count} -> {len(all_jobs)} ({dedup_count} duplicates removed)"
        )

    # Sort by match score (descending)
    all_jobs.sort(key=lambda x: x["match_score"], reverse=True)

    return all_jobs


# =============================================================================
# OUTPUT GENERATION
# =============================================================================


def save_to_csv(jobs):
    """Save jobs to CSV file"""
    filename = DATE_DIR / f"pm_jobs_{TODAY}.csv"

    fieldnames = [
        "匹配等级",
        "匹配分数",
        "数据来源",
        "职位名称",
        "公司名称",
        "职位级别",
        "工作类型",
        "远程政策",
        "薪资范围",
        "薪资下限USD",
        "薪资上限USD",
        "公司阶段",
        "融资轮次",
        "融资金额",
        "公司规模",
        "行业",
        "产品类型",
        "工作地点",
        "时区要求",
        "签证支持",
        "申请链接",
        "发布日期",
        "发布天数",
        "招聘者邮箱",
        "招聘者LinkedIn",
        "匹配亮点",
        "匹配顾虑",
        "简历重点建议",
        "面试准备要点",
    ]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for job in jobs:
            row = {
                "匹配等级": job.get("match_label", ""),
                "匹配分数": job.get("match_score", 0),
                "数据来源": job.get("source_platform", ""),
                "职位名称": job.get("job_title", ""),
                "公司名称": job.get("company_name", ""),
                "职位级别": job.get("job_level", ""),
                "工作类型": job.get("job_type", ""),
                "远程政策": job.get("remote_policy", ""),
                "薪资范围": job.get("salary_range", ""),
                "薪资下限USD": job.get("salary_min_usd", ""),
                "薪资上限USD": job.get("salary_max_usd", ""),
                "公司阶段": job.get("company_stage", ""),
                "融资轮次": job.get("funding_round", ""),
                "融资金额": job.get("funding_amount", ""),
                "公司规模": job.get("company_size", ""),
                "行业": job.get("company_industry", ""),
                "产品类型": job.get("product_type", ""),
                "工作地点": job.get("location", ""),
                "时区要求": job.get("timezone_requirements", ""),
                "签证支持": "是" if job.get("visa_sponsorship") else "否",
                "申请链接": job.get("application_url", ""),
                "发布日期": job.get("posted_date", ""),
                "发布天数": job.get("days_since_posted", ""),
                "招聘者邮箱": job.get("recruiter_email", ""),
                "招聘者LinkedIn": job.get("recruiter_linkedin", ""),
                "匹配亮点": " | ".join(job.get("match_highlights", [])),
                "匹配顾虑": " | ".join(job.get("match_concerns", [])),
                "简历重点建议": " | ".join(job.get("resume_suggestions", [])),
                "面试准备要点": " | ".join(job.get("interview_prep", [])),
            }
            writer.writerow(row)

    print(f"      CSV saved: {filename}")
    return filename


def generate_summary_report(jobs):
    """Generate summary markdown report"""
    filename = DATE_DIR / f"pm_jobs_summary_{TODAY}.md"

    user_profile = get_user_profile()

    # Calculate statistics
    total = len(jobs)
    a_level = sum(1 for j in jobs if j["match_score"] >= 80)
    b_level = sum(1 for j in jobs if 60 <= j["match_score"] < 80)
    c_level = sum(1 for j in jobs if 40 <= j["match_score"] < 60)
    d_level = sum(1 for j in jobs if j["match_score"] < 40)
    avg_score = sum(j["match_score"] for j in jobs) / total if total > 0 else 0
    remote_jobs = sum(1 for j in jobs if "remote" in j.get("remote_policy", "").lower())
    startup_jobs = sum(
        1
        for j in jobs
        if j.get("company_stage", "") in ["Seed", "Series A", "Series B"]
    )

    # Group by platform
    by_platform = {}
    for job in jobs:
        platform = job.get("source_platform", "Unknown")
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(job)

    report = f"""# PM Job Match Analysis Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**User Profile:** {user_profile["years_experience"]}+ years PM | {", ".join(user_profile["target_level"])} level | Remote preferred

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Jobs Found | {total} |
| A级 Matches (≥80) | {a_level} ({a_level / total * 100:.1f}%) |
| B级 Matches (≥60) | {b_level} ({b_level / total * 100:.1f}%) |
| C级 Matches (≥40) | {c_level} ({c_level / total * 100:.1f}%) |
| D级 Matches (<40) | {d_level} ({d_level / total * 100:.1f}%) |
| Average Match Score | {avg_score:.1f} |
| Jobs with Full Remote | {remote_jobs} ({remote_jobs / total * 100:.1f}%) |
| Early-Stage Startups | {startup_jobs} ({startup_jobs / total * 100:.1f}%) |

---

## Top 10 Best Matches

"""

    # Top 10 jobs
    for i, job in enumerate(jobs[:10], 1):
        report += f"""### {i}. {job["job_title"]} (Score: {job["match_score"]}/100)
- **Company:** {job["company_name"]} ({job.get("company_stage", "N/A")}, {job.get("funding_round", "N/A")})
- **Salary:** {job.get("salary_range", "N/A")} {"+ equity" if job.get("equity_offered") else ""}
- **Remote:** {job.get("remote_policy", "N/A")}
- **Industry:** {job.get("company_industry", "N/A")} ({job.get("product_type", "N/A")})
- **Match Highlights:**
{chr(10).join("  - " + h for h in job.get("match_highlights", []))}
- **Quick Apply:** [{job.get("application_url", "N/A")}]({job.get("application_url", "#")})
- **Resume Focus:** {job.get("resume_suggestions", ["N/A"])[0] if job.get("resume_suggestions") else "N/A"}

"""

    # By Platform
    report += """---

## By Platform

| Platform | Jobs | Avg Match Score |
|----------|------|-----------------|
"""
    for platform, platform_jobs in sorted(
        by_platform.items(), key=lambda x: -len(x[1])
    ):
        avg = sum(j["match_score"] for j in platform_jobs) / len(platform_jobs)
        report += f"| {platform} | {len(platform_jobs)} | {avg:.0f} |\n"

    # Weekly Action Plan
    report += f"""
---

## Weekly Action Plan

### This Week ({TODAY})
1. **Apply to top {min(5, a_level)} A级 matches** (highest priority)
2. **Customize resume** for {jobs[0]["company_industry"] if jobs else "target industry"} focus
3. **Research company cultures** for top matches

### Next Week
1. **Apply to remaining A级 matches**
2. **Begin B级 applications** (customize cover letters)
3. **Follow up on submitted applications**

---

*Generated by PM Job Finder Skill*
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"      Summary saved: {filename}")
    return filename


def generate_match_analysis_files(jobs):
    """Generate individual match analysis files for high-match jobs"""
    high_match_dir = DATE_DIR / "match_analysis" / "high_match"
    good_match_dir = DATE_DIR / "match_analysis" / "good_match"

    count = 0
    for job in jobs:
        if job["match_score"] < 60:
            continue

        # Determine directory
        if job["match_score"] >= 80:
            target_dir = high_match_dir
        else:
            target_dir = good_match_dir

        # Create filename
        safe_company = job["company_name"].replace(" ", "_").replace("/", "_")[:20]
        safe_title = job["job_title"].replace(" ", "_").replace("/", "_")[:30]
        filename = target_dir / f"job_{count + 1:03d}_{safe_company}_{safe_title}.md"

        content = f"""# Match Analysis: {job["job_title"]}

## Job Information
- **Company:** {job["company_name"]}
- **Position:** {job["job_title"]}
- **Level:** {job.get("job_level", "N/A")}
- **Type:** {job.get("job_type", "N/A")}
- **Remote:** {job.get("remote_policy", "N/A")}
- **Location:** {job.get("location", "N/A")}
- **Salary:** {job.get("salary_range", "N/A")}

## Company Information
- **Stage:** {job.get("company_stage", "N/A")}
- **Funding:** {job.get("funding_round", "N/A")} ({job.get("funding_amount", "N/A")})
- **Size:** {job.get("company_size", "N/A")}
- **Industry:** {job.get("company_industry", "N/A")}
- **Product Type:** {job.get("product_type", "N/A")}

---

## Match Analysis

**Overall Score:** {job["match_score"]}/100 ({job["match_label"]})

### Score Breakdown
| Dimension | Score |
|-----------|-------|
| Experience Match | {job["match_breakdown"].get("experience_match", 0)}/25 |
| Industry Match | {job["match_breakdown"].get("industry_match", 0)}/20 |
| Remote Match | {job["match_breakdown"].get("remote_match", 0)}/20 |
| Company Stage | {job["match_breakdown"].get("company_stage_match", 0)}/15 |
| Salary Match | {job["match_breakdown"].get("salary_match", 0)}/10 |
| Skills Match | {job["match_breakdown"].get("skills_match", 0)}/10 |

### Match Highlights
{chr(10).join("- " + h for h in job.get("match_highlights", ["No highlights"]))}

### Potential Concerns
{chr(10).join("- " + c for c in job.get("match_concerns", ["No concerns"]))}

---

## Application Support

### Resume Focus
{chr(10).join("- " + s for s in job.get("resume_suggestions", []))}

### Cover Letter Talking Points
{chr(10).join("- " + p for p in job.get("cover_letter_points", []))}

### Interview Preparation
{chr(10).join("- " + n for n in job.get("interview_prep", []))}

---

## Quick Links
- **Apply:** {job.get("application_url", "N/A")}
- **Recruiter Email:** {job.get("recruiter_email", "N/A")}
- **Recruiter LinkedIn:** {job.get("recruiter_linkedin", "N/A")}
- **Posted:** {job.get("posted_date", "N/A")} ({job.get("days_since_posted", 0)} days ago)

---

*Generated by PM Job Finder Skill on {TODAY}*
"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        count += 1

    print(f"      Match analysis files generated: {count}")
    return count


def save_readme():
    """Save README file with usage instructions"""
    filename = DATE_DIR / "README.md"

    content = f"""# PM Job Finder Output - {TODAY}

## Files in this folder

| File | Description |
|------|-------------|
| `pm_jobs_{TODAY}.csv` | Complete job listings with match scores |
| `pm_jobs_summary_{TODAY}.md` | Match analysis summary report |
| `match_analysis/` | Individual job match analysis files |
| `application_materials/` | Application support materials |
| `company_research/` | Company research reports |
| `company_research/company_requirements_analysis_{TODAY}.md` | **NEW** Company requirements deep analysis with 5 key research directions |

## How to use

1. **Review Summary Report** - Start with `pm_jobs_summary_{TODAY}.md` for an overview
2. **Company Deep Analysis** - Check `company_research/company_requirements_analysis_{TODAY}.md` for talent insights and research directions
3. **Filter CSV** - Use Excel/Sheets to filter by match score (A级 ≥80, B级 ≥60)
4. **Read Match Analysis** - Check `match_analysis/high_match/` for detailed analysis of top matches
5. **Apply Strategically** - Use resume suggestions and cover letter points from match analysis files

## Match Score Breakdown

- **A级 (≥80)**: Excellent match - apply immediately
- **B级 (60-79)**: Good match - strong candidate
- **C级 (40-59)**: Moderate match - consider if interested
- **D级 (<40)**: Low match - likely not ideal fit

## Generated by

PM Job Finder Skill v1.0
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main execution function"""
    print(f"\n{'=' * 60}")
    print("PM Job Finder - Data Processing & Match Analysis")
    print(f"{'=' * 60}\n")

    print("[0/6] Setting up output structure...")
    setup_output_directories()
    update_latest_symlink()
    print(f"      Output directory: {DATE_DIR}")

    print("\n[1/6] Processing jobs and calculating match scores...")
    jobs = process_jobs()
    print(f"      Total jobs processed: {len(jobs)}")
    print(f"      A级 matches: {sum(1 for j in jobs if j['match_score'] >= 80)}")
    print(f"      B级 matches: {sum(1 for j in jobs if 60 <= j['match_score'] < 80)}")

    print("\n[2/6] Saving to CSV...")
    save_to_csv(jobs)

    print("\n[3/6] Generating summary report...")
    generate_summary_report(jobs)

    print("\n[4/6] Generating match analysis files...")
    generate_match_analysis_files(jobs)

    print("\n[5/6] Running company requirements deep analysis...")
    company_analysis_result = None
    if COMPANY_ANALYZER_AVAILABLE:
        try:
            company_analysis_result, report_path = run_company_analysis(
                jobs=jobs, output_dir=DATE_DIR, use_llm=False
            )
            print(
                f"      Companies analyzed: {company_analysis_result.total_companies}"
            )
            print(f"      Report saved: {report_path}")
        except Exception as e:
            print(f"      Warning: Company analysis failed: {e}")
    else:
        print("      Skipped: company_analyzer module not available")

    print("\n[6/6] Saving README...")
    save_readme()

    companies_analyzed = (
        company_analysis_result.total_companies if company_analysis_result else "N/A"
    )

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total jobs: {len(jobs)}")
    print(f"  A级 matches (≥80): {sum(1 for j in jobs if j['match_score'] >= 80)}")
    print(f"  B级 matches (≥60): {sum(1 for j in jobs if 60 <= j['match_score'] < 80)}")
    print(f"  Average score: {sum(j['match_score'] for j in jobs) / len(jobs):.1f}")
    print(f"  Companies analyzed: {companies_analyzed}")
    print(f"\n  Quick access: output/latest/")
    print(f"  Full path: {DATE_DIR}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
