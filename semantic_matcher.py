#!/usr/bin/env python3
"""
Semantic Skill Matcher - PM Job Finder
Uses Claude API to perform semantic skill matching between job requirements and user profile.
"""

import json
import os
from typing import Dict, List, Tuple, Optional

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from user_profile import get_user_profile, SKILL_WEIGHTS


def get_anthropic_client() -> Optional[object]:
    """Get Anthropic client if available and API key is set."""
    if not ANTHROPIC_AVAILABLE:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    return Anthropic(api_key=api_key)


def calculate_semantic_skill_match(
    job_requirements: List[str],
    job_skills: List[str],
    user_profile: Dict,
    use_llm: bool = True
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate semantic skill match between job requirements and user profile.

    Args:
        job_requirements: List of job requirements
        job_skills: List of required skills
        user_profile: User profile dictionary
        use_llm: Whether to use LLM for semantic matching (falls back to keyword if False)

    Returns:
        (match_score: float 0-1, matched_skills: List[str], gaps: List[str])
    """
    if use_llm:
        client = get_anthropic_client()
        if client:
            return _llm_semantic_match(job_requirements, job_skills, user_profile, client)

    # Fallback to keyword matching
    return _keyword_match(job_skills, user_profile)


def _llm_semantic_match(
    job_requirements: List[str],
    job_skills: List[str],
    user_profile: Dict,
    client: object
) -> Tuple[float, List[str], List[str]]:
    """Use Claude API for semantic skill matching."""

    ai_agent_skills = user_profile.get('ai_agent_skills', [])
    core_skills = user_profile.get('core_skills', [])
    technical_skills = user_profile.get('technical_skills', [])
    domain_expertise = user_profile.get('domain_expertise', [])

    prompt = f"""评估候选人技能与职位要求的匹配度。

## 职位要求
{json.dumps(job_requirements, ensure_ascii=False, indent=2)}

## 职位所需技能
{json.dumps(job_skills, ensure_ascii=False, indent=2)}

## 候选人技能

### AI Agent 专项技能（权重 x1.5 - 核心差异化）
{json.dumps(ai_agent_skills, ensure_ascii=False, indent=2)}

### 核心 PM 技能（权重 x1.0）
{json.dumps(core_skills, ensure_ascii=False, indent=2)}

### 技术技能（权重 x0.8）
{json.dumps(technical_skills, ensure_ascii=False, indent=2)}

### 领域专业（权重 x1.2）
{json.dumps(domain_expertise, ensure_ascii=False, indent=2)}

## 评估规则
1. **语义匹配**: 识别语义相近但措辞不同的技能（如 "LLM Applications" ≈ "AI Agent Product Design"）
2. **可转移技能**: 评估技能的可转移性（如 "Product Strategy" 覆盖多种产品类型）
3. **经验深度**: 候选人有 10 年产品经验，能覆盖更广的技能范围
4. **AI 技能优先**: 如果职位涉及 AI/LLM/Agent，候选人的 AI Agent 专项技能应获得高匹配

## 输出格式
只输出 JSON，不要其他文字：
{{
    "score": <0-100 整数>,
    "matched_skills": ["匹配的技能1", "匹配的技能2", ...],
    "gaps": ["缺失的技能1", ...],
    "reasoning": "简短解释"
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text.strip()

        # Extract JSON from response
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)

        score = result.get("score", 50) / 100.0
        matched = result.get("matched_skills", [])
        gaps = result.get("gaps", [])

        return score, matched, gaps

    except Exception as e:
        print(f"Warning: LLM semantic match failed: {e}")
        return _keyword_match(job_skills, user_profile)


def _keyword_match(
    job_skills: List[str],
    user_profile: Dict
) -> Tuple[float, List[str], List[str]]:
    """Fallback keyword-based skill matching with weighted scoring."""

    if not job_skills:
        return 0.5, [], []

    job_skills_lower = set(s.lower() for s in job_skills)

    # Collect all user skills with their weights
    weighted_matches = []
    all_user_skills = set()

    skill_categories = [
        ('ai_agent_skills', SKILL_WEIGHTS.get('ai_agent_skills', 1.5)),
        ('core_skills', SKILL_WEIGHTS.get('core_skills', 1.0)),
        ('technical_skills', SKILL_WEIGHTS.get('technical_skills', 0.8)),
        ('domain_expertise', SKILL_WEIGHTS.get('domain_expertise', 1.2)),
    ]

    for category, weight in skill_categories:
        skills = user_profile.get(category, [])
        for skill in skills:
            skill_lower = skill.lower()
            all_user_skills.add(skill_lower)
            if skill_lower in job_skills_lower:
                weighted_matches.append((skill, weight))

    # Calculate weighted score
    if not job_skills_lower:
        return 0.5, [], []

    total_weight = sum(w for _, w in weighted_matches)
    max_possible_weight = len(job_skills_lower) * max(w for _, w in skill_categories)

    score = min(total_weight / max_possible_weight, 1.0) if max_possible_weight > 0 else 0

    matched = [s for s, _ in weighted_matches]
    gaps = [s for s in job_skills if s.lower() not in all_user_skills]

    return score, matched, gaps


def batch_semantic_match(
    jobs: List[Dict],
    user_profile: Dict = None,
    use_llm: bool = True
) -> List[Dict]:
    """
    Batch process semantic matching for multiple jobs.

    Args:
        jobs: List of job dictionaries
        user_profile: User profile (uses default if None)
        use_llm: Whether to use LLM for matching

    Returns:
        List of jobs with added semantic_match fields
    """
    if user_profile is None:
        user_profile = get_user_profile()

    for job in jobs:
        requirements = job.get('requirements', [])
        skills = job.get('skills_required', [])

        score, matched, gaps = calculate_semantic_skill_match(
            requirements, skills, user_profile, use_llm
        )

        job['semantic_skill_score'] = score
        job['semantic_matched_skills'] = matched
        job['semantic_skill_gaps'] = gaps

    return jobs


if __name__ == "__main__":
    # Test the semantic matcher
    print("=" * 60)
    print("Semantic Matcher Test")
    print("=" * 60)

    profile = get_user_profile()

    # Test job
    test_job = {
        "job_title": "Senior Product Manager - AI Platform",
        "requirements": [
            "5+ years PM experience",
            "Experience with AI/ML products",
            "Strong data analysis skills"
        ],
        "skills_required": [
            "LLM Applications",
            "Product Strategy",
            "AI/ML",
            "Data Analysis"
        ]
    }

    print("\nTest Job:")
    print(f"  Title: {test_job['job_title']}")
    print(f"  Skills: {test_job['skills_required']}")

    # Test with keyword matching
    print("\n--- Keyword Matching (Fallback) ---")
    score, matched, gaps = calculate_semantic_skill_match(
        test_job['requirements'],
        test_job['skills_required'],
        profile,
        use_llm=False
    )
    print(f"  Score: {score:.2%}")
    print(f"  Matched: {matched}")
    print(f"  Gaps: {gaps}")

    # Test with LLM matching
    client = get_anthropic_client()
    if client:
        print("\n--- LLM Semantic Matching ---")
        score, matched, gaps = calculate_semantic_skill_match(
            test_job['requirements'],
            test_job['skills_required'],
            profile,
            use_llm=True
        )
        print(f"  Score: {score:.2%}")
        print(f"  Matched: {matched}")
        print(f"  Gaps: {gaps}")
    else:
        print("\n⚠️ Claude API not available (set ANTHROPIC_API_KEY)")

    print("\n" + "=" * 60)
