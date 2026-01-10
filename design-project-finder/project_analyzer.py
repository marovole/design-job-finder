#!/usr/bin/env python3
"""
Project Requirements Analyzer Module
项目需求深度分析：提取技术需求、推断痛点、检测项目阶段

Features:
- Deep analysis of project requirements
- Pain point inference from context
- Project stage detection
- Deliverable extraction
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Tuple
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectStage(Enum):
    """项目阶段"""
    GREENFIELD = "greenfield"       # 全新项目
    REDESIGN = "redesign"           # 重新设计
    ENHANCEMENT = "enhancement"     # 功能增强
    AUDIT = "audit"                 # 设计审计/评估
    MAINTENANCE = "maintenance"     # 维护/迭代
    UNKNOWN = "unknown"


class UrgencyLevel(Enum):
    """紧急程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class TeamSize(Enum):
    """团队规模"""
    SOLO = "solo"                   # 个人/小团队
    SMALL = "small"                 # 5-20人
    MEDIUM = "medium"               # 20-100人
    LARGE = "large"                 # 100-500人
    ENTERPRISE = "enterprise"       # 500+
    UNKNOWN = "unknown"


@dataclass
class ProjectAnalysis:
    """项目分析结果"""
    # 基础信息
    project_id: str = ""
    project_title: str = ""
    client_name: str = ""
    industry: str = ""

    # 技术需求
    technical_needs: List[str] = field(default_factory=list)

    # 推断的痛点
    pain_points: List[str] = field(default_factory=list)

    # 项目阶段
    project_stage: ProjectStage = ProjectStage.UNKNOWN

    # 期望的交付物
    expected_deliverables: List[str] = field(default_factory=list)

    # 紧急程度
    urgency: UrgencyLevel = UrgencyLevel.UNKNOWN

    # 团队规模推断
    team_size: TeamSize = TeamSize.UNKNOWN

    # 匹配的关键词
    matched_keywords: Dict[str, List[str]] = field(default_factory=dict)

    # 额外信息
    work_scope: List[str] = field(default_factory=list)
    platform: str = ""
    budget_range: str = ""

    def to_dict(self) -> dict:
        return {
            'project_id': self.project_id,
            'project_title': self.project_title,
            'client_name': self.client_name,
            'industry': self.industry,
            'technical_needs': self.technical_needs,
            'pain_points': self.pain_points,
            'project_stage': self.project_stage.value,
            'expected_deliverables': self.expected_deliverables,
            'urgency': self.urgency.value,
            'team_size': self.team_size.value,
            'matched_keywords': self.matched_keywords,
            'work_scope': self.work_scope,
            'platform': self.platform,
            'budget_range': self.budget_range
        }


# ============================================
# Keyword Patterns
# ============================================

# 技术需求关键词
TECHNICAL_KEYWORDS = {
    'dashboard': ['dashboard', 'dashboards', 'admin panel', 'control panel'],
    'analytics': ['analytics', 'data analysis', 'reporting', 'metrics', 'insights'],
    'data_visualization': ['data visualization', 'charts', 'graphs', 'infographics'],
    'design_system': ['design system', 'component library', 'ui kit', 'pattern library'],
    'mobile_app': ['mobile app', 'ios app', 'android app', 'mobile design', 'app design'],
    'web_app': ['web app', 'web application', 'web platform', 'saas'],
    'responsive': ['responsive', 'responsive design', 'mobile-first', 'adaptive'],
    'accessibility': ['accessibility', 'a11y', 'wcag', 'ada compliance', 'inclusive design'],
    'user_research': ['user research', 'user testing', 'usability testing', 'ux research'],
    'prototyping': ['prototype', 'prototyping', 'interactive prototype', 'hi-fi prototype'],
    'wireframing': ['wireframe', 'wireframing', 'low-fi', 'lo-fi'],
    'information_architecture': ['information architecture', 'ia', 'site map', 'navigation'],
    'interaction_design': ['interaction design', 'ixd', 'micro-interactions', 'animations'],
    'b2b': ['b2b', 'business to business', 'enterprise', 'b2b saas'],
    'ecommerce': ['ecommerce', 'e-commerce', 'online store', 'shopping', 'checkout'],
    'fintech': ['fintech', 'financial', 'banking', 'payments', 'trading'],
    'healthcare': ['healthcare', 'health tech', 'medical', 'patient', 'clinical'],
}

# 痛点推断规则
PAIN_POINT_PATTERNS = {
    'scaling_design': [
        r'scale|scaling|grow|growing|expand|multiple\s*teams?',
        r'enterprise|global|international'
    ],
    'design_consistency': [
        r'design\s*system|component|consistent|consistency|unified',
        r'style\s*guide|brand\s*guidelines'
    ],
    'complex_data': [
        r'dashboard|analytics|data|metrics|reporting',
        r'visualization|complex\s*data'
    ],
    'user_onboarding': [
        r'onboarding|new\s*user|activation|first\s*time',
        r'getting\s*started|tutorial'
    ],
    'accessibility_compliance': [
        r'accessibility|wcag|ada|a11y|inclusive',
        r'compliance|regulations?'
    ],
    'legacy_modernization': [
        r'redesign|modernize|update|refresh|revamp',
        r'legacy|outdated|old\s*system'
    ],
    'user_trust': [
        r'trust|security|privacy|confidence',
        r'fintech|finance|banking|payment'
    ],
    'feature_discovery': [
        r'feature|discovery|engagement|adoption',
        r'navigation|findability'
    ],
}

# 项目阶段关键词
STAGE_KEYWORDS = {
    ProjectStage.GREENFIELD: [
        'from scratch', 'new product', 'new app', 'greenfield',
        'build from ground up', '0 to 1', 'zero to one', 'launch'
    ],
    ProjectStage.REDESIGN: [
        'redesign', 'revamp', 'overhaul', 'refresh', 'rebrand',
        'complete redesign', 'new look', 'modernize'
    ],
    ProjectStage.ENHANCEMENT: [
        'enhance', 'improve', 'add feature', 'new feature',
        'upgrade', 'optimize', 'extend', 'expand'
    ],
    ProjectStage.AUDIT: [
        'audit', 'review', 'assessment', 'evaluate', 'analysis',
        'ux audit', 'design review', 'heuristic'
    ],
    ProjectStage.MAINTENANCE: [
        'maintain', 'support', 'bug fix', 'iteration',
        'ongoing', 'continuous', 'regular updates'
    ],
}

# 紧急程度关键词
URGENCY_KEYWORDS = {
    UrgencyLevel.HIGH: [
        'urgent', 'asap', 'immediately', 'rush', 'critical',
        'deadline', 'fast turnaround', 'quickly'
    ],
    UrgencyLevel.MEDIUM: [
        'soon', 'timely', 'within weeks', 'next month'
    ],
    UrgencyLevel.LOW: [
        'flexible', 'no rush', 'when available', 'long-term'
    ],
}

# 交付物关键词
DELIVERABLE_KEYWORDS = {
    'wireframes': ['wireframe', 'wireframes', 'low-fidelity'],
    'mockups': ['mockup', 'mockups', 'high-fidelity', 'hi-fi', 'visual design'],
    'prototypes': ['prototype', 'prototypes', 'interactive', 'clickable'],
    'design_system': ['design system', 'component library', 'ui kit'],
    'user_flows': ['user flow', 'user journey', 'task flow'],
    'personas': ['persona', 'user persona', 'user profiles'],
    'research_report': ['research report', 'findings', 'insights report'],
    'specifications': ['specs', 'specifications', 'handoff', 'dev handoff'],
    'style_guide': ['style guide', 'brand guidelines', 'visual guidelines'],
}


class ProjectRequirementsAnalyzer:
    """
    项目需求分析器

    从项目描述中提取深层需求和痛点
    """

    def __init__(self, user_profile: dict = None):
        self.user_profile = user_profile or {}

    def analyze(self, project: dict) -> ProjectAnalysis:
        """
        分析项目需求

        Args:
            project: 项目数据字典

        Returns:
            ProjectAnalysis: 分析结果
        """
        # 提取基本信息
        project_id = project.get('id', project.get('client', 'unknown'))
        title = project.get('title', '')
        client = project.get('client', '')
        requirements = project.get('requirements', '')
        industry = project.get('industry', '')
        work_scope = project.get('work_scope', [])

        # 合并所有文本用于分析
        full_text = self._combine_text(project)

        # 创建分析结果
        analysis = ProjectAnalysis(
            project_id=project_id,
            project_title=title,
            client_name=client,
            industry=industry,
            work_scope=work_scope if isinstance(work_scope, list) else [work_scope],
            platform=project.get('platform', ''),
            budget_range=project.get('budget', '')
        )

        # 1. 提取技术需求
        analysis.technical_needs = self._extract_technical_needs(full_text)
        analysis.matched_keywords = self._get_matched_keywords(full_text)

        # 2. 推断痛点
        analysis.pain_points = self._infer_pain_points(
            full_text, industry, analysis.technical_needs
        )

        # 3. 检测项目阶段
        analysis.project_stage = self._detect_project_stage(full_text, title)

        # 4. 提取交付物
        analysis.expected_deliverables = self._extract_deliverables(full_text)

        # 5. 判断紧急程度
        analysis.urgency = self._detect_urgency(full_text)

        # 6. 推断团队规模
        analysis.team_size = self._infer_team_size(full_text, client)

        return analysis

    def _combine_text(self, project: dict) -> str:
        """合并项目中的所有文本字段"""
        text_fields = [
            project.get('title', ''),
            project.get('requirements', ''),
            project.get('description', ''),
            project.get('skills_required', ''),
        ]

        # 处理列表字段
        work_scope = project.get('work_scope', [])
        if isinstance(work_scope, list):
            text_fields.extend(work_scope)
        else:
            text_fields.append(str(work_scope))

        deliverables = project.get('deliverables', [])
        if isinstance(deliverables, list):
            text_fields.extend(deliverables)
        else:
            text_fields.append(str(deliverables))

        return ' '.join(str(f) for f in text_fields if f).lower()

    def _extract_technical_needs(self, text: str) -> List[str]:
        """提取技术需求"""
        needs = []

        for need_type, keywords in TECHNICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    # 转换为可读格式
                    readable = need_type.replace('_', ' ').title()
                    if readable not in needs:
                        needs.append(readable)
                    break

        return needs

    def _get_matched_keywords(self, text: str) -> Dict[str, List[str]]:
        """获取匹配的关键词详情"""
        matched = {}

        for need_type, keywords in TECHNICAL_KEYWORDS.items():
            found = []
            for keyword in keywords:
                if keyword.lower() in text:
                    found.append(keyword)
            if found:
                matched[need_type] = found

        return matched

    def _infer_pain_points(
        self,
        text: str,
        industry: str,
        technical_needs: List[str]
    ) -> List[str]:
        """
        推断项目痛点

        基于文本内容、行业和技术需求推断可能的痛点
        """
        pain_points = []

        # 基于模式匹配推断
        for pain_point, patterns in PAIN_POINT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    readable = self._pain_point_to_readable(pain_point)
                    if readable not in pain_points:
                        pain_points.append(readable)
                    break

        # 基于行业添加常见痛点
        industry_pain_points = self._get_industry_pain_points(industry)
        for point in industry_pain_points:
            if point not in pain_points:
                pain_points.append(point)

        # 基于技术需求添加相关痛点
        needs_pain_points = self._get_needs_based_pain_points(technical_needs)
        for point in needs_pain_points:
            if point not in pain_points:
                pain_points.append(point)

        return pain_points[:5]  # 限制数量

    def _pain_point_to_readable(self, pain_point: str) -> str:
        """将痛点代码转换为可读文本"""
        mapping = {
            'scaling_design': 'Scaling design across teams',
            'design_consistency': 'Maintaining design consistency',
            'complex_data': 'Making complex data understandable',
            'user_onboarding': 'Improving user onboarding',
            'accessibility_compliance': 'Meeting accessibility compliance',
            'legacy_modernization': 'Modernizing legacy systems',
            'user_trust': 'Building user trust',
            'feature_discovery': 'Improving feature discovery',
        }
        return mapping.get(pain_point, pain_point.replace('_', ' ').title())

    def _get_industry_pain_points(self, industry: str) -> List[str]:
        """获取行业特定的痛点"""
        industry_lower = industry.lower() if industry else ''

        industry_mapping = {
            'fintech': [
                'Regulatory compliance in UX',
                'Building user trust with financial data'
            ],
            'finance': [
                'Regulatory compliance in UX',
                'Building user trust with financial data'
            ],
            'healthcare': [
                'HIPAA compliance considerations',
                'Improving patient experience'
            ],
            'health': [
                'HIPAA compliance considerations',
                'Improving patient experience'
            ],
            'saas': [
                'User onboarding optimization',
                'Feature discovery and adoption'
            ],
            'b2b': [
                'Complex workflow simplification',
                'Power user vs. new user balance'
            ],
            'ecommerce': [
                'Conversion rate optimization',
                'Cart abandonment reduction'
            ],
            'edtech': [
                'Engagement and retention',
                'Learning experience optimization'
            ],
        }

        for key, points in industry_mapping.items():
            if key in industry_lower:
                return points

        return []

    def _get_needs_based_pain_points(self, technical_needs: List[str]) -> List[str]:
        """基于技术需求推断痛点"""
        pain_points = []

        needs_mapping = {
            'Dashboard': 'Making complex data understandable',
            'Analytics': 'Data-driven decision making support',
            'Design System': 'Maintaining design consistency at scale',
            'Accessibility': 'Meeting accessibility compliance',
            'B2B': 'Complex workflow simplification',
            'Ecommerce': 'Conversion optimization',
        }

        for need in technical_needs:
            if need in needs_mapping:
                pain_points.append(needs_mapping[need])

        return pain_points

    def _detect_project_stage(self, text: str, title: str) -> ProjectStage:
        """检测项目阶段"""
        combined = f"{title} {text}".lower()

        # 按优先级检测
        for stage, keywords in STAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in combined:
                    return stage

        # 默认推断
        if 'new' in combined or 'create' in combined or 'build' in combined:
            return ProjectStage.GREENFIELD

        return ProjectStage.UNKNOWN

    def _extract_deliverables(self, text: str) -> List[str]:
        """提取期望的交付物"""
        deliverables = []

        for deliverable, keywords in DELIVERABLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    readable = deliverable.replace('_', ' ').title()
                    if readable not in deliverables:
                        deliverables.append(readable)
                    break

        return deliverables

    def _detect_urgency(self, text: str) -> UrgencyLevel:
        """检测紧急程度"""
        for level, keywords in URGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return level

        return UrgencyLevel.UNKNOWN

    def _infer_team_size(self, text: str, client: str) -> TeamSize:
        """推断客户团队规模"""
        combined = f"{text} {client}".lower()

        # 企业级关键词
        if any(kw in combined for kw in ['enterprise', 'fortune 500', 'global', 'multinational']):
            return TeamSize.ENTERPRISE

        if any(kw in combined for kw in ['large team', 'multiple teams', 'corporation']):
            return TeamSize.LARGE

        if any(kw in combined for kw in ['growing company', 'mid-size', 'series b', 'series c']):
            return TeamSize.MEDIUM

        if any(kw in combined for kw in ['startup', 'small team', 'seed', 'series a', 'early stage']):
            return TeamSize.SMALL

        if any(kw in combined for kw in ['solo', 'individual', 'freelance', 'personal']):
            return TeamSize.SOLO

        return TeamSize.UNKNOWN


# ============================================
# Convenience Functions
# ============================================

def analyze_project(project: dict) -> ProjectAnalysis:
    """快速分析项目需求"""
    analyzer = ProjectRequirementsAnalyzer()
    return analyzer.analyze(project)


def analyze_batch(projects: List[dict]) -> List[ProjectAnalysis]:
    """批量分析项目"""
    analyzer = ProjectRequirementsAnalyzer()
    return [analyzer.analyze(p) for p in projects]


# ============================================
# CLI Entry Point
# ============================================

def main():
    """命令行测试入口"""
    import json

    # 测试项目
    test_project = {
        'id': 'test-1',
        'client': 'TechStartup Inc',
        'title': 'Senior UX Designer for SaaS Dashboard Redesign',
        'industry': 'SaaS',
        'requirements': '''
        We need an experienced UX designer to help redesign our analytics dashboard.
        The product serves enterprise clients and needs to scale across multiple teams.
        Key focus areas:
        - Data visualization and complex metrics display
        - Design system development
        - Accessibility compliance (WCAG 2.1 AA)
        - User onboarding flow optimization
        ''',
        'work_scope': ['Dashboard Design', 'Design System', 'User Research'],
        'deliverables': ['Wireframes', 'High-fidelity mockups', 'Interactive prototype'],
        'budget': '$10,000 - $15,000'
    }

    analyzer = ProjectRequirementsAnalyzer()
    result = analyzer.analyze(test_project)

    print("\n" + "=" * 60)
    print("PROJECT ANALYSIS RESULT")
    print("=" * 60)
    print(f"\nProject: {result.project_title}")
    print(f"Client: {result.client_name}")
    print(f"Industry: {result.industry}")

    print(f"\nTechnical Needs:")
    for need in result.technical_needs:
        print(f"  • {need}")

    print(f"\nInferred Pain Points:")
    for point in result.pain_points:
        print(f"  • {point}")

    print(f"\nProject Stage: {result.project_stage.value}")
    print(f"Urgency: {result.urgency.value}")
    print(f"Team Size: {result.team_size.value}")

    print(f"\nExpected Deliverables:")
    for deliverable in result.expected_deliverables:
        print(f"  • {deliverable}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
