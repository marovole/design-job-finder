#!/usr/bin/env python3
"""
Company Requirements Deep Analyzer - PM Job Finder
Analyzes job requirements across companies to identify talent patterns and research directions.

Features:
- Aggregate jobs by company
- Extract requirement patterns (skills, experience, soft skills)
- Generate company talent profiles
- Cross-company comparison analysis
- Generate 5 key research directions
- Skill gap analysis for user

Version: 1.0
Date: 2026-01-11
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re

from user_profile import get_user_profile

# =============================================================================
# CONSTANTS
# =============================================================================

# Common soft skills keywords
SOFT_SKILLS_KEYWORDS = [
    "communication",
    "leadership",
    "collaboration",
    "teamwork",
    "influence",
    "stakeholder",
    "cross-functional",
    "presentation",
    "negotiation",
    "problem-solving",
    "analytical",
    "strategic thinking",
    "empathy",
    "adaptability",
    "ownership",
    "accountability",
    "initiative",
    "mentoring",
]

# Leadership indicators
LEADERSHIP_KEYWORDS = [
    "lead",
    "manage",
    "mentor",
    "coach",
    "direct",
    "supervise",
    "guide",
    "build team",
    "grow team",
    "hire",
    "develop team",
    "people management",
    "influence",
    "drive alignment",
    "executive",
    "stakeholder",
]

# Technical skills categories
TECHNICAL_SKILL_CATEGORIES = {
    "AI/ML": [
        "ai",
        "ml",
        "machine learning",
        "llm",
        "gpt",
        "ai agent",
        "nlp",
        "deep learning",
        "neural",
        "generative ai",
    ],
    "Data": [
        "data analysis",
        "sql",
        "analytics",
        "metrics",
        "a/b testing",
        "experimentation",
        "data-driven",
        "tableau",
        "looker",
    ],
    "Technical": [
        "api",
        "python",
        "javascript",
        "engineering",
        "architecture",
        "system design",
        "technical pm",
    ],
    "Product": [
        "product strategy",
        "roadmap",
        "user research",
        "ux",
        "design",
        "prototyping",
        "figma",
        "wireframes",
    ],
    "Growth": [
        "growth",
        "acquisition",
        "retention",
        "funnel",
        "conversion",
        "ltv",
        "cac",
        "viral",
    ],
    "Platform": [
        "platform",
        "infrastructure",
        "developer tools",
        "sdk",
        "devex",
        "internal tools",
        "b2b saas",
    ],
}

# Experience type patterns
EXPERIENCE_PATTERNS = {
    "0-1": [
        "0 to 1",
        "0-1",
        "from scratch",
        "greenfield",
        "build from ground",
        "new product",
        "launch new",
    ],
    "1-N Scaling": [
        "scale",
        "growth stage",
        "rapid growth",
        "hypergrowth",
        "millions of users",
        "high scale",
    ],
    "Platform": [
        "platform",
        "infrastructure",
        "developer",
        "api",
        "sdk",
        "internal tools",
    ],
    "AI/ML": ["ai", "ml", "machine learning", "llm", "generative", "model"],
    "B2B Enterprise": ["enterprise", "b2b", "saas", "business customers", "corporate"],
    "Consumer": [
        "consumer",
        "b2c",
        "mobile app",
        "social",
        "marketplace",
        "e-commerce",
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class CompanyJobGroup:
    """Grouped jobs by company."""

    company_name: str
    normalized_name: str
    jobs: List[Dict]
    job_count: int
    company_info: Dict = field(default_factory=dict)


@dataclass
class RequirementPattern:
    """Extracted requirement patterns from jobs."""

    skill_frequency: Dict[str, int]
    technical_skills: Dict[str, int]  # Categorized technical skills
    soft_skills: List[str]
    leadership_indicators: List[str]
    experience_requirements: List[str]
    valued_experiences: Dict[str, int]  # Experience type -> count
    years_required: List[int]


@dataclass
class CompanyTalentProfile:
    """Ideal candidate profile for a company."""

    company_name: str
    jobs_analyzed: int
    company_stage: str
    company_industry: str
    ideal_candidate_summary: str
    must_have_skills: List[str]
    nice_to_have_skills: List[str]
    experience_profile: str
    leadership_level: str  # Low/Medium/High
    culture_fit_indicators: List[str]
    hiring_priorities: List[str]
    avg_match_score: float
    top_job_titles: List[str]


@dataclass
class ResearchDirection:
    """One of the 5 key research directions."""

    direction_id: int
    title: str
    description: str
    key_findings: List[str]
    actionable_insights: List[str]
    priority: str  # "高" / "中" / "低"
    user_action_items: List[str]
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanyAnalysisResult:
    """Complete analysis result container."""

    date: str
    total_companies: int
    total_jobs: int
    company_groups: List[CompanyJobGroup]
    company_profiles: List[CompanyTalentProfile]
    cross_company_patterns: Dict
    research_directions: List[ResearchDirection]
    skill_gap_analysis: Dict


# =============================================================================
# CORE ANALYSIS FUNCTIONS
# =============================================================================


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for deduplication and grouping.

    Args:
        name: Raw company name

    Returns:
        Normalized lowercase name without common suffixes
    """
    if not name:
        return "unknown"

    name = name.lower().strip()

    # Remove common suffixes
    suffixes = [
        " inc",
        " inc.",
        " llc",
        " ltd",
        " ltd.",
        " limited",
        " corp",
        " corp.",
        " corporation",
        " ug",
        " gmbh",
        " co.",
        " co",
        " company",
        " technologies",
        " technology",
        " labs",
        " ai",
        " io",
        ", inc",
        ", llc",
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)]

    # Remove special characters
    name = re.sub(r"[^\w\s]", "", name)
    name = " ".join(name.split())  # Normalize whitespace

    return name.strip()


def aggregate_by_company(jobs: List[Dict]) -> List[CompanyJobGroup]:
    """
    Aggregate jobs by company name.

    Args:
        jobs: List of job dictionaries

    Returns:
        List of CompanyJobGroup sorted by job count descending
    """
    company_map = defaultdict(list)

    for job in jobs:
        company = job.get("company_name", "Unknown")
        normalized = normalize_company_name(company)
        company_map[normalized].append(job)

    groups = []
    for normalized_name, company_jobs in company_map.items():
        # Use the most common original name
        original_names = Counter(j.get("company_name", "") for j in company_jobs)
        best_name = (
            original_names.most_common(1)[0][0] if original_names else normalized_name
        )

        # Aggregate company info from jobs
        company_info = _aggregate_company_info(company_jobs)

        groups.append(
            CompanyJobGroup(
                company_name=best_name,
                normalized_name=normalized_name,
                jobs=company_jobs,
                job_count=len(company_jobs),
                company_info=company_info,
            )
        )

    # Sort by job count descending
    groups.sort(key=lambda g: g.job_count, reverse=True)
    return groups


def _aggregate_company_info(jobs: List[Dict]) -> Dict:
    """Extract consolidated company info from multiple job listings."""
    info = {
        "stages": [],
        "industries": [],
        "sizes": [],
        "funding_rounds": [],
        "product_types": [],
        "remote_policies": [],
    }

    for job in jobs:
        if job.get("company_stage"):
            info["stages"].append(job["company_stage"])
        if job.get("company_industry"):
            info["industries"].append(job["company_industry"])
        if job.get("company_size"):
            info["sizes"].append(job["company_size"])
        if job.get("funding_round"):
            info["funding_rounds"].append(job["funding_round"])
        if job.get("product_type"):
            info["product_types"].append(job["product_type"])
        if job.get("remote_policy"):
            info["remote_policies"].append(job["remote_policy"])

    # Get most common values
    result = {}
    for key, values in info.items():
        if values:
            result[key.rstrip("s")] = Counter(values).most_common(1)[0][0]

    return result


def extract_requirement_patterns(company_jobs: List[Dict]) -> RequirementPattern:
    """
    Extract requirement patterns from a company's job listings.

    Args:
        company_jobs: List of jobs from the same company

    Returns:
        RequirementPattern with extracted patterns
    """
    # Collect all text for analysis
    all_skills = []
    all_requirements = []
    all_responsibilities = []
    all_descriptions = []

    for job in company_jobs:
        skills = job.get("skills_required", [])
        if isinstance(skills, list):
            all_skills.extend([s.lower().strip() for s in skills])

        requirements = job.get("requirements", [])
        if isinstance(requirements, list):
            all_requirements.extend(requirements)

        responsibilities = job.get("responsibilities", [])
        if isinstance(responsibilities, list):
            all_responsibilities.extend(responsibilities)

        desc = job.get("job_description", "")
        if desc:
            all_descriptions.append(desc)

    # Combine all text for pattern matching
    all_text = " ".join(
        all_requirements + all_responsibilities + all_descriptions
    ).lower()

    # 1. Skill frequency
    skill_freq = Counter(all_skills)

    # 2. Technical skills by category
    technical_skills = _categorize_technical_skills(all_skills, all_text)

    # 3. Soft skills extraction
    soft_skills = _extract_soft_skills(all_text)

    # 4. Leadership indicators
    leadership = _extract_leadership_indicators(all_text)

    # 5. Experience requirements and years
    exp_reqs, years = _extract_experience_requirements(all_requirements)

    # 6. Valued experience types
    valued_exp = _identify_valued_experiences(all_text)

    return RequirementPattern(
        skill_frequency=dict(skill_freq.most_common(20)),
        technical_skills=technical_skills,
        soft_skills=list(set(soft_skills))[:10],
        leadership_indicators=list(set(leadership))[:10],
        experience_requirements=list(set(exp_reqs))[:10],
        valued_experiences=valued_exp,
        years_required=years,
    )


def _categorize_technical_skills(skills: List[str], full_text: str) -> Dict[str, int]:
    """Categorize skills into technical categories."""
    category_counts = defaultdict(int)

    for category, keywords in TECHNICAL_SKILL_CATEGORIES.items():
        for keyword in keywords:
            # Count in explicit skills
            for skill in skills:
                if keyword in skill:
                    category_counts[category] += 1
            # Count in full text
            if keyword in full_text:
                category_counts[category] += full_text.count(keyword)

    return dict(category_counts)


def _extract_soft_skills(text: str) -> List[str]:
    """Extract soft skills from text."""
    found = []
    for skill in SOFT_SKILLS_KEYWORDS:
        if skill in text:
            found.append(skill)
    return found


def _extract_leadership_indicators(text: str) -> List[str]:
    """Extract leadership-related requirements."""
    found = []
    for indicator in LEADERSHIP_KEYWORDS:
        if indicator in text:
            found.append(indicator)
    return found


def _extract_experience_requirements(
    requirements: List[str],
) -> Tuple[List[str], List[int]]:
    """Extract experience requirements and year numbers."""
    exp_reqs = []
    years = []

    year_pattern = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)", re.IGNORECASE)

    for req in requirements:
        req_lower = req.lower()

        # Check if it's an experience requirement
        if any(
            kw in req_lower
            for kw in ["experience", "years", "background", "track record"]
        ):
            exp_reqs.append(req)

            # Extract year numbers
            matches = year_pattern.findall(req)
            for match in matches:
                try:
                    years.append(int(match))
                except ValueError:
                    pass

    return exp_reqs, years


def _identify_valued_experiences(text: str) -> Dict[str, int]:
    """Identify valued experience types from text."""
    valued = {}

    for exp_type, keywords in EXPERIENCE_PATTERNS.items():
        count = 0
        for keyword in keywords:
            count += text.count(keyword)
        if count > 0:
            valued[exp_type] = count

    return valued


def generate_company_profile(
    company_name: str, jobs: List[Dict], patterns: RequirementPattern
) -> CompanyTalentProfile:
    """
    Generate a talent profile for a company.

    Args:
        company_name: Company name
        jobs: Jobs from this company
        patterns: Extracted requirement patterns

    Returns:
        CompanyTalentProfile describing ideal candidate
    """
    # Get company info
    company_info = _aggregate_company_info(jobs)

    # Calculate average match score
    scores = [j.get("match_score", 0) for j in jobs]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Determine must-have vs nice-to-have skills
    skill_items = sorted(patterns.skill_frequency.items(), key=lambda x: -x[1])
    total_jobs = len(jobs)

    must_have = [s for s, c in skill_items if c >= total_jobs * 0.6][:5]
    nice_to_have = [s for s, c in skill_items if c < total_jobs * 0.6 and c >= 2][:5]

    # Determine leadership level
    leadership_count = len(patterns.leadership_indicators)
    if leadership_count >= 5:
        leadership_level = "高"
    elif leadership_count >= 2:
        leadership_level = "中"
    else:
        leadership_level = "低"

    # Determine experience profile
    exp_profile = _generate_experience_profile(patterns)

    # Generate ideal candidate summary
    summary = _generate_candidate_summary(
        company_name, company_info, must_have, patterns, leadership_level
    )

    # Extract hiring priorities
    priorities = _extract_hiring_priorities(jobs)

    # Get top job titles
    titles = Counter(j.get("job_title", "") for j in jobs)
    top_titles = [t for t, _ in titles.most_common(3)]

    return CompanyTalentProfile(
        company_name=company_name,
        jobs_analyzed=len(jobs),
        company_stage=company_info.get("stage", "Unknown"),
        company_industry=company_info.get("industry", "Unknown"),
        ideal_candidate_summary=summary,
        must_have_skills=must_have,
        nice_to_have_skills=nice_to_have,
        experience_profile=exp_profile,
        leadership_level=leadership_level,
        culture_fit_indicators=patterns.soft_skills[:5],
        hiring_priorities=priorities,
        avg_match_score=round(avg_score, 1),
        top_job_titles=top_titles,
    )


def _generate_experience_profile(patterns: RequirementPattern) -> str:
    """Generate experience profile description."""
    parts = []

    # Years of experience
    if patterns.years_required:
        avg_years = sum(patterns.years_required) / len(patterns.years_required)
        parts.append(f"{avg_years:.0f}+ 年产品经验")

    # Top valued experience types
    if patterns.valued_experiences:
        top_exp = sorted(patterns.valued_experiences.items(), key=lambda x: -x[1])[:2]
        exp_types = [e[0] for e in top_exp]
        parts.append(f"偏好 {', '.join(exp_types)} 经验")

    # Technical emphasis
    if patterns.technical_skills:
        top_tech = sorted(patterns.technical_skills.items(), key=lambda x: -x[1])[:2]
        tech_types = [t[0] for t in top_tech]
        parts.append(f"技术重点: {', '.join(tech_types)}")

    return " | ".join(parts) if parts else "综合型产品经理"


def _generate_candidate_summary(
    company_name: str,
    company_info: Dict,
    must_have: List[str],
    patterns: RequirementPattern,
    leadership_level: str,
) -> str:
    """Generate a natural language summary of ideal candidate."""
    stage = company_info.get("stage", "")
    industry = company_info.get("industry", "")

    # Build summary parts
    parts = []

    # Years
    if patterns.years_required:
        avg = sum(patterns.years_required) / len(patterns.years_required)
        parts.append(f"{avg:.0f}+ 年经验的资深PM")
    else:
        parts.append("有经验的产品经理")

    # Stage-specific
    if "seed" in stage.lower() or "series a" in stage.lower():
        parts.append("适应从0到1创业环境")
    elif "growth" in stage.lower() or "series c" in stage.lower():
        parts.append("具备规模化增长经验")

    # Industry
    if industry:
        parts.append(f"熟悉{industry}行业")

    # Technical
    if patterns.technical_skills.get("AI/ML", 0) > 3:
        parts.append("具备AI/ML产品经验")
    elif patterns.technical_skills.get("Data", 0) > 3:
        parts.append("数据驱动型思维")

    # Leadership
    if leadership_level == "高":
        parts.append("有团队管理经验")

    return "，".join(parts) + "。"


def _extract_hiring_priorities(jobs: List[Dict]) -> List[str]:
    """Extract hiring priorities from job data."""
    priorities = []

    # Recent postings = higher priority
    for job in jobs:
        days = job.get("days_since_posted", 999)
        title = job.get("job_title", "")
        if days <= 7:
            priorities.append(f"紧急招聘: {title}")

    # Level distribution
    levels = Counter(j.get("job_level", "") for j in jobs)
    top_level = levels.most_common(1)
    if top_level:
        priorities.append(f"主要招聘 {top_level[0][0]} 级别")

    return priorities[:3]


def cross_company_analysis(
    company_groups: List[CompanyJobGroup], company_profiles: List[CompanyTalentProfile]
) -> Dict:
    """
    Perform cross-company comparison analysis.

    Args:
        company_groups: List of company job groups
        company_profiles: List of company talent profiles

    Returns:
        Dictionary with cross-company insights
    """
    total_companies = len(company_profiles)

    # 1. Universal requirements (appear in 80%+ companies)
    universal_skills = _find_universal_requirements(company_profiles, threshold=0.8)
    common_skills = _find_universal_requirements(company_profiles, threshold=0.5)

    # 2. Skill frequency across all companies
    all_skills = []
    for profile in company_profiles:
        all_skills.extend(profile.must_have_skills)
        all_skills.extend(profile.nice_to_have_skills)
    skill_freq = Counter(all_skills)

    # 3. Technical skill trends
    tech_trends = _analyze_technical_trends(company_groups)

    # 4. Experience type distribution
    exp_distribution = _analyze_experience_distribution(company_groups)

    # 5. Leadership requirements distribution
    leadership_dist = Counter(p.leadership_level for p in company_profiles)

    # 6. Company clustering
    clusters = _cluster_companies(company_profiles)

    # 7. Calculate percentages for key skills
    ai_companies = sum(
        1
        for p in company_profiles
        if any(
            "ai" in s.lower() or "ml" in s.lower()
            for s in p.must_have_skills + p.nice_to_have_skills
        )
    )
    data_companies = sum(
        1
        for p in company_profiles
        if any(
            "data" in s.lower() or "analytics" in s.lower()
            for s in p.must_have_skills + p.nice_to_have_skills
        )
    )

    return {
        "total_companies": total_companies,
        "total_jobs": sum(g.job_count for g in company_groups),
        "universal_requirements": universal_skills,
        "common_skills": common_skills,
        "skill_frequency": dict(skill_freq.most_common(20)),
        "technical_trends": tech_trends,
        "experience_distribution": exp_distribution,
        "leadership_distribution": dict(leadership_dist),
        "company_clusters": clusters,
        "ai_skill_percentage": ai_companies / total_companies
        if total_companies > 0
        else 0,
        "data_skill_percentage": data_companies / total_companies
        if total_companies > 0
        else 0,
    }


def _find_universal_requirements(
    profiles: List[CompanyTalentProfile], threshold: float = 0.8
) -> List[str]:
    """Find skills that appear in threshold% of companies."""
    skill_company_count = defaultdict(int)

    for profile in profiles:
        seen = set()
        for skill in profile.must_have_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                skill_company_count[skill] += 1
                seen.add(skill_lower)

    total = len(profiles)
    threshold_count = total * threshold

    universal = [
        skill
        for skill, count in skill_company_count.items()
        if count >= threshold_count
    ]

    return universal


def _analyze_technical_trends(company_groups: List[CompanyJobGroup]) -> Dict[str, int]:
    """Analyze technical skill trends across companies."""
    trends = defaultdict(int)

    for group in company_groups:
        patterns = extract_requirement_patterns(group.jobs)
        for category, count in patterns.technical_skills.items():
            if count > 0:
                trends[category] += 1  # Count companies, not mentions

    return dict(sorted(trends.items(), key=lambda x: -x[1]))


def _analyze_experience_distribution(
    company_groups: List[CompanyJobGroup],
) -> Dict[str, int]:
    """Analyze valued experience type distribution."""
    distribution = defaultdict(int)

    for group in company_groups:
        patterns = extract_requirement_patterns(group.jobs)
        for exp_type, count in patterns.valued_experiences.items():
            if count > 0:
                distribution[exp_type] += 1

    return dict(sorted(distribution.items(), key=lambda x: -x[1]))


def _cluster_companies(profiles: List[CompanyTalentProfile]) -> Dict[str, List[str]]:
    """Cluster companies by their requirements similarity."""
    clusters = {
        "AI-First": [],
        "Developer Tools": [],
        "Growth Focus": [],
        "Enterprise B2B": [],
        "Consumer": [],
        "General": [],
    }

    for profile in profiles:
        skills_text = " ".join(
            profile.must_have_skills + profile.nice_to_have_skills
        ).lower()
        industry = profile.company_industry.lower() if profile.company_industry else ""

        # Classify into clusters
        if any(kw in skills_text for kw in ["ai", "ml", "llm", "machine learning"]):
            clusters["AI-First"].append(profile.company_name)
        elif any(
            kw in skills_text or kw in industry
            for kw in ["developer", "api", "platform", "sdk"]
        ):
            clusters["Developer Tools"].append(profile.company_name)
        elif any(
            kw in skills_text
            for kw in ["growth", "acquisition", "funnel", "conversion"]
        ):
            clusters["Growth Focus"].append(profile.company_name)
        elif "b2b" in industry or "enterprise" in industry or "saas" in industry:
            clusters["Enterprise B2B"].append(profile.company_name)
        elif "consumer" in industry or "b2c" in industry:
            clusters["Consumer"].append(profile.company_name)
        else:
            clusters["General"].append(profile.company_name)

    # Remove empty clusters
    return {k: v for k, v in clusters.items() if v}


def generate_research_directions(
    cross_analysis: Dict,
    company_profiles: List[CompanyTalentProfile],
    user_profile: Dict,
) -> List[ResearchDirection]:
    """
    Generate 5 key research directions with actionable insights.

    Args:
        cross_analysis: Cross-company analysis results
        company_profiles: List of company talent profiles
        user_profile: User profile configuration

    Returns:
        List of 5 ResearchDirection objects
    """
    directions = []

    # Direction 1: Most in-demand technical skills
    directions.append(_direction_1_technical_skills(cross_analysis, company_profiles))

    # Direction 2: Most valued project experience types
    directions.append(_direction_2_project_experience(cross_analysis, company_profiles))

    # Direction 3: Leadership and soft skills patterns
    directions.append(
        _direction_3_leadership_soft_skills(cross_analysis, company_profiles)
    )

    # Direction 4: Industry-specific requirements
    directions.append(_direction_4_industry_specific(cross_analysis, company_profiles))

    # Direction 5: Emerging trends (AI, Data, etc.)
    directions.append(_direction_5_emerging_trends(cross_analysis, company_profiles))

    return directions


def _direction_1_technical_skills(analysis: Dict, profiles: List) -> ResearchDirection:
    """Direction 1: Most in-demand technical skills."""
    tech_trends = analysis.get("technical_trends", {})
    skill_freq = analysis.get("skill_frequency", {})

    # Find top technical areas
    top_tech = sorted(tech_trends.items(), key=lambda x: -x[1])[:5]

    key_findings = []
    if top_tech:
        key_findings.append(
            f"{top_tech[0][0]} 技能在 {top_tech[0][1]} 家公司的职位中出现"
        )

    ai_pct = analysis.get("ai_skill_percentage", 0)
    if ai_pct > 0:
        key_findings.append(f"AI/ML 相关技能出现在 {ai_pct * 100:.0f}% 的公司职位中")

    data_pct = analysis.get("data_skill_percentage", 0)
    if data_pct > 0:
        key_findings.append(f"数据分析能力出现在 {data_pct * 100:.0f}% 的公司职位中")

    # Add skill frequency insights
    top_skills = list(skill_freq.keys())[:5]
    if top_skills:
        key_findings.append(f"最常见的技能要求: {', '.join(top_skills[:3])}")

    return ResearchDirection(
        direction_id=1,
        title="最需求的技术技能",
        description="基于职位数据分析，识别市场上PM最需要掌握的技术能力",
        key_findings=key_findings,
        actionable_insights=[
            "掌握基础的AI/ML产品知识已成为标配，非技术背景PM也需了解LLM基础",
            "SQL + 数据分析工具组合是跨行业的基础要求",
            "API和系统设计理解能帮助与工程团队更有效协作",
        ],
        priority="高",
        user_action_items=[
            "完成一个AI产品相关的项目案例或学习经历",
            "强化SQL和数据分析能力，能独立做产品数据分析",
            "了解RESTful API和系统架构基础概念",
        ],
        supporting_data={
            "tech_trends": tech_trends,
            "skill_frequency": dict(list(skill_freq.items())[:10]),
        },
    )


def _direction_2_project_experience(
    analysis: Dict, profiles: List
) -> ResearchDirection:
    """Direction 2: Most valued project experience types."""
    exp_dist = analysis.get("experience_distribution", {})

    # Sort by frequency
    top_exp = sorted(exp_dist.items(), key=lambda x: -x[1])

    key_findings = []
    for exp_type, count in top_exp[:3]:
        key_findings.append(f"{exp_type} 经验被 {count} 家公司重视")

    if not key_findings:
        key_findings.append("项目经验要求因公司而异，建议针对目标公司定制")

    return ResearchDirection(
        direction_id=2,
        title="最受重视的项目经验类型",
        description="分析什么类型的产品经验最受各公司青睐",
        key_findings=key_findings,
        actionable_insights=[
            "0-1 项目经验在早期创业公司最受重视，证明能在模糊环境中交付",
            "规模化增长经验对成长期公司更有吸引力",
            "平台/基础设施经验是技术型PM的差异化优势",
        ],
        priority="高",
        user_action_items=[
            "整理过往项目，按0-1/增长/平台等维度分类准备案例",
            "量化项目成果：用户增长X%，收入提升Y%，效率提高Z%",
            "准备STAR格式的项目故事，每个项目2-3分钟版本",
        ],
        supporting_data={"experience_distribution": exp_dist},
    )


def _direction_3_leadership_soft_skills(
    analysis: Dict, profiles: List
) -> ResearchDirection:
    """Direction 3: Leadership and soft skills patterns."""
    leadership_dist = analysis.get("leadership_distribution", {})

    # Calculate high leadership requirement percentage
    total = sum(leadership_dist.values())
    high_leadership = leadership_dist.get("高", 0)
    high_pct = high_leadership / total * 100 if total > 0 else 0

    key_findings = [
        f"{high_pct:.0f}% 的公司对领导力有高要求",
        "跨职能协作能力是最普遍的软技能要求",
        "影响力（Influence）比直接管理权更被强调",
    ]

    return ResearchDirection(
        direction_id=3,
        title="领导力与软技能模式",
        description="提取对PM领导力和沟通协作的具体要求模式",
        key_findings=key_findings,
        actionable_insights=[
            "即使是IC角色，也需要展示跨团队推动项目的能力",
            "Stakeholder management 是高级PM的核心能力",
            "数据驱动的说服力比权威更有效",
        ],
        priority="中",
        user_action_items=[
            "准备2-3个展示跨职能领导力的具体案例",
            "练习用数据支持决策的表达方式",
            "总结与工程/设计团队协作的最佳实践经验",
        ],
        supporting_data={"leadership_distribution": leadership_dist},
    )


def _direction_4_industry_specific(analysis: Dict, profiles: List) -> ResearchDirection:
    """Direction 4: Industry-specific requirements."""
    clusters = analysis.get("company_clusters", {})

    key_findings = []
    for cluster_name, companies in clusters.items():
        if companies:
            key_findings.append(
                f"{cluster_name} 类公司: {len(companies)} 家 ({', '.join(companies[:3])}...)"
            )

    if not key_findings:
        key_findings.append("公司类型多样化，建议选择1-2个重点行业深耕")

    return ResearchDirection(
        direction_id=4,
        title="行业特定要求",
        description="不同行业和公司类型的特殊PM需求",
        key_findings=key_findings[:5],
        actionable_insights=[
            "ToB SaaS 强调客户生命周期管理和企业销售配合",
            "ToC Consumer 更看重用户直觉和增长经验",
            "Developer Tools 需要技术深度和开发者同理心",
        ],
        priority="中",
        user_action_items=[
            "确定1-2个目标行业，深入研究行业动态",
            "建立目标行业的人脉网络",
            "准备行业特定的产品案例和观点",
        ],
        supporting_data={"company_clusters": clusters},
    )


def _direction_5_emerging_trends(analysis: Dict, profiles: List) -> ResearchDirection:
    """Direction 5: Emerging trends (AI, Data, etc.)."""
    ai_pct = analysis.get("ai_skill_percentage", 0)
    tech_trends = analysis.get("technical_trends", {})

    key_findings = [
        f"AI/ML 已成为 {ai_pct * 100:.0f}% 公司的核心要求",
        "LLM/Generative AI 产品经验是2026年最大的加分项",
        "数据驱动决策从加分项变成基础要求",
    ]

    # Add specific trend data
    ai_count = tech_trends.get("AI/ML", 0)
    if ai_count > 0:
        key_findings.append(f"{ai_count} 家公司明确要求AI/ML相关技能")

    return ResearchDirection(
        direction_id=5,
        title="新兴趋势: AI与数据",
        description="AI、数据等新兴领域对PM的需求趋势",
        key_findings=key_findings,
        actionable_insights=[
            "即使不做AI产品，也需要理解AI如何赋能产品",
            "Prompt Engineering 正在成为PM的基础技能",
            "AI Agent 和自动化工作流是下一个增长点",
        ],
        priority="高",
        user_action_items=[
            "学习LLM基础知识，理解Prompt Engineering",
            "关注AI产品案例，思考如何应用到自己的领域",
            "尝试使用AI工具提升工作效率，积累使用经验",
            "考虑参与AI相关的side project或开源贡献",
        ],
        supporting_data={"ai_percentage": ai_pct, "tech_trends": tech_trends},
    )


def analyze_skill_gaps(
    company_profiles: List[CompanyTalentProfile], user_profile: Dict
) -> Dict:
    """
    Analyze skill gaps between user profile and market requirements.

    Args:
        company_profiles: List of company talent profiles
        user_profile: User's current profile

    Returns:
        Skill gap analysis dictionary
    """
    # Collect all required skills
    all_must_have = []
    all_nice_to_have = []

    for profile in company_profiles:
        all_must_have.extend(profile.must_have_skills)
        all_nice_to_have.extend(profile.nice_to_have_skills)

    must_have_freq = Counter(all_must_have)
    nice_to_have_freq = Counter(all_nice_to_have)

    # Get user skills
    user_skills = set()
    for skill_list in [
        user_profile.get("core_skills", []),
        user_profile.get("technical_skills", []),
        user_profile.get("ai_agent_skills", []),
    ]:
        user_skills.update(s.lower() for s in skill_list)

    # Find gaps
    gaps = []
    for skill, count in must_have_freq.most_common(15):
        skill_lower = skill.lower()
        # Check if user has this skill (fuzzy match)
        has_skill = any(skill_lower in us or us in skill_lower for us in user_skills)

        if not has_skill:
            priority = "高" if count >= len(company_profiles) * 0.5 else "中"
            gaps.append(
                {
                    "skill": skill,
                    "demand_count": count,
                    "demand_percentage": count / len(company_profiles) * 100,
                    "priority": priority,
                }
            )

    # Find strengths
    strengths = []
    for skill in user_skills:
        # Check how many companies want this skill
        match_count = sum(1 for s in all_must_have if skill in s.lower())
        if match_count > 0:
            strengths.append({"skill": skill, "market_demand": match_count})

    return {
        "skill_gaps": gaps[:10],
        "strengths": sorted(strengths, key=lambda x: -x["market_demand"])[:10],
        "market_must_haves": dict(must_have_freq.most_common(10)),
        "market_nice_to_haves": dict(nice_to_have_freq.most_common(10)),
        "user_skill_coverage": len(strengths) / len(must_have_freq) * 100
        if must_have_freq
        else 0,
    }


# =============================================================================
# REPORT GENERATION
# =============================================================================


def generate_company_report(
    analysis_result: CompanyAnalysisResult, output_dir: Path
) -> Path:
    """
    Generate comprehensive company analysis report.

    Args:
        analysis_result: Complete analysis results
        output_dir: Output directory path

    Returns:
        Path to generated report file
    """
    # Ensure company_research directory exists
    report_dir = output_dir / "company_research"
    report_dir.mkdir(parents=True, exist_ok=True)

    filename = report_dir / f"company_requirements_analysis_{analysis_result.date}.md"

    # Generate report sections
    sections = []

    # Header
    sections.append(f"""# 公司需求深度分析报告

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**分析基础**: {analysis_result.total_jobs} 个职位 | {analysis_result.total_companies} 家公司

---
""")

    # Section 1: Executive Summary
    sections.append(_generate_executive_summary(analysis_result))

    # Section 2: Company-by-Company Analysis
    sections.append(
        _generate_company_by_company_section(analysis_result.company_profiles[:10])
    )

    # Section 3: Cross-Company Patterns
    sections.append(
        _generate_cross_company_section(analysis_result.cross_company_patterns)
    )

    # Section 4: 5 Key Research Directions
    sections.append(
        _generate_research_directions_section(analysis_result.research_directions)
    )

    # Section 5: Talent Profile Recommendations
    sections.append(
        _generate_talent_recommendations_section(analysis_result.company_profiles[:5])
    )

    # Section 6: Skill Gap Analysis
    sections.append(_generate_skill_gap_section(analysis_result.skill_gap_analysis))

    # Footer
    sections.append(f"""
---

*报告由 PM Job Finder v1.1 自动生成*
*分析日期: {analysis_result.date}*
""")

    # Write report
    report_content = "\n".join(sections)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)

    return filename


def _generate_executive_summary(result: CompanyAnalysisResult) -> str:
    """Generate executive summary section."""
    cross = result.cross_company_patterns
    directions = result.research_directions
    gaps = result.skill_gap_analysis

    # Top skills
    top_skills = list(cross.get("skill_frequency", {}).keys())[:3]
    top_skills_str = ", ".join(top_skills) if top_skills else "N/A"

    # Top experience types
    top_exp = list(cross.get("experience_distribution", {}).keys())[:2]
    top_exp_str = ", ".join(top_exp) if top_exp else "N/A"

    # User coverage
    coverage = gaps.get("user_skill_coverage", 0)

    return f"""## 1. Executive Summary

### 关键数据

| 指标 | 数值 |
|------|------|
| 分析公司数 | {result.total_companies} |
| 分析职位数 | {result.total_jobs} |
| AI相关职位比例 | {cross.get("ai_skill_percentage", 0) * 100:.0f}% |
| 数据技能要求比例 | {cross.get("data_skill_percentage", 0) * 100:.0f}% |

### 核心发现

1. **技术技能**: {top_skills_str}
2. **经验偏好**: {top_exp_str}
3. **领导力要求**: {cross.get("leadership_distribution", {}).get("高", 0)} 家公司有高领导力要求
4. **新兴趋势**: AI/ML 技能需求持续增长

### 用户匹配概览

- **当前技能覆盖率**: {coverage:.1f}%
- **需要提升的领域**: {", ".join(g["skill"] for g in gaps.get("skill_gaps", [])[:3])}

---
"""


def _generate_company_by_company_section(profiles: List[CompanyTalentProfile]) -> str:
    """Generate company-by-company analysis section."""
    section = """## 2. Company-by-Company Analysis

"""

    for i, profile in enumerate(profiles, 1):
        must_have_str = (
            "\n".join(f"- {s}" for s in profile.must_have_skills) or "- 未明确"
        )
        nice_to_have_str = (
            "\n".join(f"- {s}" for s in profile.nice_to_have_skills) or "- 未明确"
        )
        priorities_str = (
            "\n".join(f"{j + 1}. {p}" for j, p in enumerate(profile.hiring_priorities))
            or "1. 未明确"
        )

        section += f"""### {i}. {profile.company_name} ({profile.jobs_analyzed}个职位)

**公司概况**
- 融资阶段: {profile.company_stage}
- 行业: {profile.company_industry}
- 平均匹配分: {profile.avg_match_score}

**人才需求画像**
> {profile.ideal_candidate_summary}

**必备技能 (Must-Have)**
{must_have_str}

**加分技能 (Nice-to-Have)**
{nice_to_have_str}

**经验要求**
{profile.experience_profile}

**领导力要求**: {profile.leadership_level}

**招聘优先级**
{priorities_str}

---

"""

    return section


def _generate_cross_company_section(cross_analysis: Dict) -> str:
    """Generate cross-company patterns section."""
    # Universal requirements
    universal = cross_analysis.get("universal_requirements", [])
    universal_str = (
        "\n".join(f"| {s} | 80%+ | ★★★★★ |" for s in universal[:5]) or "| 无 | - | - |"
    )

    # Skill frequency table
    skill_freq = cross_analysis.get("skill_frequency", {})
    skill_rows = []
    for skill, count in list(skill_freq.items())[:10]:
        skill_rows.append(f"| {skill} | {count} |")
    skill_table = "\n".join(skill_rows) or "| 无数据 | - |"

    # Company clusters
    clusters = cross_analysis.get("company_clusters", {})
    cluster_section = ""
    for cluster_name, companies in clusters.items():
        if companies:
            companies_str = ", ".join(companies[:5])
            if len(companies) > 5:
                companies_str += f"... (+{len(companies) - 5})"
            cluster_section += f"""
**{cluster_name}**
- 公司: {companies_str}
- 数量: {len(companies)} 家
"""

    return f"""## 3. Cross-Company Patterns

### 3.1 通用要求 (出现在80%+公司)

| 技能/要求 | 覆盖率 | 重要性 |
|-----------|--------|--------|
{universal_str}

### 3.2 技能需求频率

| 技能 | 出现次数 |
|------|----------|
{skill_table}

### 3.3 公司聚类分析
{cluster_section}

---
"""


def _generate_research_directions_section(directions: List[ResearchDirection]) -> str:
    """Generate 5 key research directions section."""
    section = """## 4. 五大研究方向

"""

    priority_stars = {"高": "⭐⭐⭐⭐⭐", "中": "⭐⭐⭐⭐", "低": "⭐⭐⭐"}

    for d in directions:
        findings_str = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(d.key_findings))
        insights_str = "\n".join(f"- {i}" for i in d.actionable_insights)
        actions_str = "\n".join(f"- [ ] {a}" for a in d.user_action_items)

        section += f"""### 方向{d.direction_id}: {d.title} {priority_stars.get(d.priority, "")}

**描述**: {d.description}

**关键发现**
{findings_str}

**可执行洞察**
{insights_str}

**用户行动建议**
{actions_str}

---

"""

    return section


def _generate_talent_recommendations_section(
    profiles: List[CompanyTalentProfile],
) -> str:
    """Generate talent profile recommendations section."""
    section = """## 5. 人才画像建议

### 针对Top匹配公司的准备策略

"""

    for profile in profiles:
        section += f"""**{profile.company_name}**

> {profile.ideal_candidate_summary}

**面试准备重点**:
1. 准备 {profile.company_industry} 行业相关案例
2. 强调 {", ".join(profile.must_have_skills[:3])} 相关经验
3. 展示 {profile.experience_profile}

---

"""

    return section


def _generate_skill_gap_section(gap_analysis: Dict) -> str:
    """Generate skill gap analysis section."""
    # Gaps table
    gaps = gap_analysis.get("skill_gaps", [])
    gap_rows = []
    for g in gaps[:10]:
        gap_rows.append(
            f"| {g['skill']} | {g['demand_percentage']:.0f}% | {g['priority']} |"
        )
    gap_table = "\n".join(gap_rows) or "| 无明显差距 | - | - |"

    # Strengths
    strengths = gap_analysis.get("strengths", [])
    strength_rows = []
    for s in strengths[:5]:
        strength_rows.append(f"| {s['skill']} | {s['market_demand']} |")
    strength_table = "\n".join(strength_rows) or "| 未识别 | - |"

    coverage = gap_analysis.get("user_skill_coverage", 0)

    return f"""## 6. 技能差距分析

### 当前技能市场覆盖率: {coverage:.1f}%

### 6.1 需要提升的技能

| 技能 | 市场需求度 | 优先级 |
|------|------------|--------|
{gap_table}

### 6.2 当前优势技能

| 技能 | 市场需求次数 |
|------|--------------|
{strength_table}

### 6.3 提升建议

**高优先级 (1个月内)**
1. 针对上表中"高"优先级技能，制定学习计划
2. 通过项目实践积累相关经验

**中优先级 (3个月内)**
1. 拓展"中"优先级技能的了解
2. 建立相关领域的知识体系

**长期发展 (6个月+)**
1. 持续关注行业趋势变化
2. 建立目标行业的专业网络

---
"""


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def run_company_analysis(
    jobs: List[Dict],
    output_dir: Path,
    use_llm: bool = False,  # Reserved for future LLM enhancement
) -> Tuple[CompanyAnalysisResult, Path]:
    """
    Run complete company requirements analysis workflow.

    Args:
        jobs: List of processed job dictionaries
        output_dir: Output directory for reports
        use_llm: Whether to use LLM for enhanced analysis (future)

    Returns:
        Tuple of (CompanyAnalysisResult, report_file_path)
    """
    print("      [1/6] Aggregating jobs by company...")
    company_groups = aggregate_by_company(jobs)
    print(f"            Found {len(company_groups)} unique companies")

    print("      [2/6] Extracting requirement patterns...")
    patterns_by_company = {}
    for group in company_groups:
        patterns_by_company[group.company_name] = extract_requirement_patterns(
            group.jobs
        )

    print("      [3/6] Generating company talent profiles...")
    company_profiles = []
    for group in company_groups:
        patterns = patterns_by_company[group.company_name]
        profile = generate_company_profile(group.company_name, group.jobs, patterns)
        company_profiles.append(profile)

    print("      [4/6] Performing cross-company analysis...")
    cross_patterns = cross_company_analysis(company_groups, company_profiles)

    print("      [5/6] Generating 5 key research directions...")
    user_profile = get_user_profile()
    research_directions = generate_research_directions(
        cross_patterns, company_profiles, user_profile
    )

    print("      [6/6] Analyzing skill gaps...")
    skill_gaps = analyze_skill_gaps(company_profiles, user_profile)

    # Create result object
    today = datetime.now().strftime("%Y-%m-%d")
    result = CompanyAnalysisResult(
        date=today,
        total_companies=len(company_groups),
        total_jobs=len(jobs),
        company_groups=company_groups,
        company_profiles=company_profiles,
        cross_company_patterns=cross_patterns,
        research_directions=research_directions,
        skill_gap_analysis=skill_gaps,
    )

    # Generate report
    print("      Generating company analysis report...")
    report_path = generate_company_report(result, output_dir)

    return result, report_path


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # For standalone testing
    print("Company Analyzer - Standalone Test")
    print("=" * 50)

    # Import sample data from process_pm_jobs
    try:
        from process_pm_jobs import (
            pm_jobs_data,
            process_jobs,
            DATE_DIR,
            setup_output_directories,
        )

        setup_output_directories()
        jobs = process_jobs()

        result, report_path = run_company_analysis(jobs, DATE_DIR)

        print(f"\nAnalysis Complete!")
        print(f"  Companies analyzed: {result.total_companies}")
        print(f"  Jobs analyzed: {result.total_jobs}")
        print(f"  Report saved: {report_path}")

    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("Please run from the PM-job-finder directory.")
