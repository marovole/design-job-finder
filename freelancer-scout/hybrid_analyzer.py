#!/usr/bin/env python3
"""
Hybrid Analyzer Module
Features:
- Extracts Technical (Dev) & Product (PM) requirements
- Infers "One-Person Army" suitability
- Detects project stage (0-1 vs Maintenance)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectStage(Enum):
    GREENFIELD = "greenfield"       # 0-1 New Build (Best for you)
    MVP_RESCUE = "mvp_rescue"       # "My dev disappeared"
    SCALE_UP = "scale_up"           # Post-PMF
    MAINTENANCE = "maintenance"     # Boring
    UNKNOWN = "unknown"

@dataclass
class ProjectAnalysis:
    project_title: str = ""
    client_name: str = ""
    # Hybrid Specifics
    dev_needs: List[str] = field(default_factory=list)
    pm_needs: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    project_stage: ProjectStage = ProjectStage.UNKNOWN
    is_fuzzy: bool = False  # If requirements are vague (Good for PM)

    def to_dict(self) -> dict:
        return {
            'project_title': self.project_title,
            'client_name': self.client_name,
            'dev_needs': self.dev_needs,
            'pm_needs': self.pm_needs,
            'pain_points': self.pain_points,
            'project_stage': self.project_stage.value,
            'is_fuzzy': self.is_fuzzy
        }

# ============================================
# Keyword Patterns (Hybrid)
# ============================================

DEV_KEYWORDS = {
    'Full-stack': ['full stack', 'fullstack', 'full-stack', 'end-to-end'],
    'Frontend': ['react', 'next.js', 'vue', 'tailwind', 'frontend', 'ui implementation'],
    'Backend': ['python', 'fastapi', 'node', 'django', 'backend', 'api', 'database', 'sql'],
    'Mobile': ['react native', 'flutter', 'ios', 'android', 'mobile app'],
    'AI/LLM': ['llm', 'openai', 'langchain', 'ai agent', 'chatbot', 'nlp'],
}

PM_KEYWORDS = {
    'MVP Strategy': ['mvp', 'minimum viable product', 'prototype', 'proof of concept'],
    'Product Management': ['product manager', 'roadmap', 'user stories', 'requirements', 'specs'],
    'Discovery': ['user research', 'market fit', 'validation', 'discovery'],
}

PAIN_POINT_PATTERNS = {
    'fuzzy_requirements': [
        r'have an idea', r'no specs', r'not sure technical', r'need guidance', r'consulting'
    ],
    'speed_need': [
        r'launch fast', r'asap', r'deadline', r'weeks', r'yesterday'
    ],
    'missing_cto': [
        r'non-technical', r'looking for cto', r'tech partner', r'technical co-founder'
    ],
    'messy_code': [
        r'refactor', r'legacy', r'spaghetti', r'fix bugs', r'slow'
    ]
}

class HybridAnalyzer:
    def analyze(self, project: dict) -> ProjectAnalysis:
        title = project.get('title', '')
        desc = project.get('description', '')
        reqs = project.get('requirements', '')
        full_text = f"{title} {desc} {reqs}".lower()

        analysis = ProjectAnalysis(
            project_title=title,
            client_name=project.get('client', 'Unknown')
        )

        # 1. Extract Dev Needs
        for cat, kws in DEV_KEYWORDS.items():
            if any(k in full_text for k in kws):
                analysis.dev_needs.append(cat)

        # 2. Extract PM Needs
        for cat, kws in PM_KEYWORDS.items():
            if any(k in full_text for k in kws):
                analysis.pm_needs.append(cat)

        # 3. Infer Pain Points
        for pp, patterns in PAIN_POINT_PATTERNS.items():
            if any(re.search(p, full_text) for p in patterns):
                analysis.pain_points.append(pp)

        # 4. Detect Stage
        if any(w in full_text for w in ['from scratch', 'new idea', '0-1', 'greenfield', 'mvp']):
            analysis.project_stage = ProjectStage.GREENFIELD
        elif 'refactor' in full_text or 'legacy' in full_text:
            analysis.project_stage = ProjectStage.MAINTENANCE
        elif 'scale' in full_text or 'growth' in full_text:
            analysis.project_stage = ProjectStage.SCALE_UP

        # 5. Check Fuzziness (The "I have an idea" factor)
        # If high match on PM needs or "idea" keywords but low on specific tech constraints
        if 'idea' in full_text and len(analysis.dev_needs) < 2:
            analysis.is_fuzzy = True

        return analysis

def analyze_project(project: dict) -> ProjectAnalysis:
    return HybridAnalyzer().analyze(project)
