#!/usr/bin/env python3
"""
Achievement Matcher Module
用户成就智能匹配：匹配项目需求与用户作品集

Features:
- Multi-dimensional relevance scoring
- Metric extraction based on project needs
- Pitch angle determination
- Multiple achievement matching
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from pathlib import Path
import yaml
import logging

# Handle both package and standalone imports
try:
    from .project_analyzer import ProjectAnalysis, ProjectStage
except ImportError:
    from project_analyzer import ProjectAnalysis, ProjectStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PitchAngle(Enum):
    """推销角度"""
    DATA_VISUALIZATION = "data_visualization_expert"
    ENTERPRISE_SYSTEM = "enterprise_system_expert"
    MERCHANT_PLATFORM = "merchant_platform_expert"
    MOBILE_CONSUMER = "mobile_consumer_expert"
    DESIGN_SYSTEM = "design_system_expert"
    B2B_SAAS = "b2b_saas_expert"
    GENERAL = "general_senior_designer"


@dataclass
class RelevantAchievement:
    """相关成就匹配结果"""
    project_name: str
    project_name_cn: str = ""
    benchmark: str = ""
    result: str = ""
    result_en: str = ""
    relevance_score: float = 0.0
    relevant_metrics: List[str] = field(default_factory=list)
    pitch_angle: PitchAngle = PitchAngle.GENERAL
    match_reasons: List[str] = field(default_factory=list)
    keywords_matched: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'project_name': self.project_name,
            'project_name_cn': self.project_name_cn,
            'benchmark': self.benchmark,
            'result': self.result,
            'result_en': self.result_en,
            'relevance_score': self.relevance_score,
            'relevant_metrics': self.relevant_metrics,
            'pitch_angle': self.pitch_angle.value,
            'match_reasons': self.match_reasons,
            'keywords_matched': self.keywords_matched
        }


@dataclass
class MatchResult:
    """匹配结果"""
    top_achievement: Optional[RelevantAchievement] = None
    all_achievements: List[RelevantAchievement] = field(default_factory=list)
    primary_pitch_angle: PitchAngle = PitchAngle.GENERAL
    combined_metrics: List[str] = field(default_factory=list)
    match_summary: str = ""

    def to_dict(self) -> dict:
        return {
            'top_achievement': self.top_achievement.to_dict() if self.top_achievement else None,
            'all_achievements': [a.to_dict() for a in self.all_achievements],
            'primary_pitch_angle': self.primary_pitch_angle.value,
            'combined_metrics': self.combined_metrics,
            'match_summary': self.match_summary
        }


# ============================================
# Default User Profile (Huang Rong)
# ============================================

DEFAULT_HIGHLIGHT_PROJECTS = [
    {
        'name': 'HUAWEI Analytics',
        'name_cn': '华为分析',
        'benchmark': 'Google Analytics',
        'result': '全球接入 21,000+ 应用，海外 15,520+ 应用',
        'result_en': '21,000+ apps integrated globally, 15,520+ overseas',
        'keywords': ['analytics', 'data', 'dashboard', 'tracking', 'metrics',
                    'visualization', 'reporting', 'insights'],
        'pitch_angle': PitchAngle.DATA_VISUALIZATION
    },
    {
        'name': 'Business Connect',
        'name_cn': '商家联盟',
        'benchmark': 'Google My Business',
        'result': '接入商家 594 万，CP 110 家',
        'result_en': '5.94 million merchants, 110 content providers',
        'keywords': ['merchant', 'local', 'business', 'commerce', 'listing',
                    'directory', 'store', 'shop'],
        'pitch_angle': PitchAngle.MERCHANT_PLATFORM
    },
    {
        'name': 'Huawei Cloud Billing Center',
        'name_cn': '华为云费用中心',
        'benchmark': 'AWS Billing Console',
        'result': '企业级云服务费用管理系统',
        'result_en': 'Enterprise cloud billing management system',
        'keywords': ['cloud', 'billing', 'enterprise', 'fintech', 'cost',
                    'management', 'b2b', 'saas'],
        'pitch_angle': PitchAngle.ENTERPRISE_SYSTEM
    },
    {
        'name': 'HarmonyOS Service Console',
        'name_cn': '鸿蒙元服务管理台',
        'benchmark': 'Google Play Console',
        'result': '开发者后台管理系统',
        'result_en': 'Developer console and service management',
        'keywords': ['developer', 'console', 'admin', 'platform', 'management',
                    'portal', 'backend'],
        'pitch_angle': PitchAngle.ENTERPRISE_SYSTEM
    },
    {
        'name': 'Matchbox App',
        'name_cn': '火柴盒 App',
        'benchmark': 'Consumer Mobile App',
        'result': 'App Store 热推前七，最美应用推荐，完成天使轮融资',
        'result_en': 'Top 7 on App Store, featured by Best Apps, angel round funded',
        'keywords': ['mobile', 'consumer', 'startup', 'app', 'ios', 'android'],
        'pitch_angle': PitchAngle.MOBILE_CONSUMER
    },
]


class AchievementMatcher:
    """
    成就匹配器

    将项目需求与用户成就进行智能匹配
    """

    def __init__(self, user_profile: dict = None):
        self.user_profile = user_profile or {}
        self.highlights = self._load_highlights()

    def _load_highlights(self) -> List[dict]:
        """加载用户亮点项目"""
        # 首先尝试从 user_profile 加载
        if self.user_profile.get('highlight_projects'):
            return self.user_profile['highlight_projects']

        # 尝试从配置文件加载
        config_path = Path(__file__).parent / "user_profile.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config.get('highlight_projects'):
                        return config['highlight_projects']
            except Exception as e:
                logger.warning(f"Failed to load user profile: {e}")

        # 使用默认值
        return DEFAULT_HIGHLIGHT_PROJECTS

    def match(self, analysis: ProjectAnalysis) -> MatchResult:
        """
        匹配项目需求与用户成就

        Args:
            analysis: 项目分析结果

        Returns:
            MatchResult: 匹配结果
        """
        all_achievements = []

        for highlight in self.highlights:
            relevance = self._calculate_relevance(highlight, analysis)
            if relevance.relevance_score > 0.1:  # 阈值
                all_achievements.append(relevance)

        # 按相关度排序
        all_achievements.sort(key=lambda x: x.relevance_score, reverse=True)

        # 取前3个
        top_achievements = all_achievements[:3]

        # 确定主要推销角度
        primary_angle = self._determine_primary_angle(top_achievements, analysis)

        # 合并相关指标
        combined_metrics = self._combine_metrics(top_achievements)

        # 生成匹配摘要
        summary = self._generate_summary(top_achievements, analysis)

        return MatchResult(
            top_achievement=top_achievements[0] if top_achievements else None,
            all_achievements=top_achievements,
            primary_pitch_angle=primary_angle,
            combined_metrics=combined_metrics,
            match_summary=summary
        )

    def _calculate_relevance(
        self,
        highlight: dict,
        analysis: ProjectAnalysis
    ) -> RelevantAchievement:
        """
        计算成就与项目的相关度

        评分维度：
        - 关键词匹配
        - 痛点相关性
        - 行业相关性
        - 项目阶段匹配
        """
        score = 0.0
        match_reasons = []
        keywords_matched = []

        highlight_keywords = highlight.get('keywords', [])
        highlight_name = highlight.get('name', '')

        # 1. 关键词匹配 (最高 0.4)
        keyword_score, matched = self._score_keyword_match(
            highlight_keywords, analysis
        )
        score += keyword_score * 0.4
        keywords_matched.extend(matched)
        if matched:
            match_reasons.append(f"Keywords: {', '.join(matched[:3])}")

        # 2. 痛点相关性 (最高 0.3)
        pain_point_score = self._score_pain_point_match(highlight, analysis)
        score += pain_point_score * 0.3
        if pain_point_score > 0:
            match_reasons.append("Addresses project pain points")

        # 3. 行业相关性 (最高 0.2)
        industry_score = self._score_industry_match(highlight, analysis)
        score += industry_score * 0.2
        if industry_score > 0:
            match_reasons.append(f"Industry relevance: {analysis.industry}")

        # 4. 项目阶段匹配 (最高 0.1)
        stage_score = self._score_stage_match(highlight, analysis)
        score += stage_score * 0.1

        # 提取相关指标
        relevant_metrics = self._extract_relevant_metrics(highlight, analysis)

        # 确定推销角度
        pitch_angle = self._get_pitch_angle(highlight)

        return RelevantAchievement(
            project_name=highlight_name,
            project_name_cn=highlight.get('name_cn', ''),
            benchmark=highlight.get('benchmark', ''),
            result=highlight.get('result', ''),
            result_en=highlight.get('result_en', ''),
            relevance_score=min(score, 1.0),
            relevant_metrics=relevant_metrics,
            pitch_angle=pitch_angle,
            match_reasons=match_reasons,
            keywords_matched=keywords_matched
        )

    def _score_keyword_match(
        self,
        highlight_keywords: List[str],
        analysis: ProjectAnalysis
    ) -> Tuple[float, List[str]]:
        """计算关键词匹配得分"""
        if not highlight_keywords:
            return 0.0, []

        # 收集项目中的所有关键词
        project_keywords = set()

        # 从技术需求中提取
        for need in analysis.technical_needs:
            project_keywords.add(need.lower())

        # 从匹配的关键词中提取
        for kw_list in analysis.matched_keywords.values():
            for kw in kw_list:
                project_keywords.add(kw.lower())

        # 从标题和行业中提取
        project_keywords.add(analysis.project_title.lower())
        project_keywords.add(analysis.industry.lower())

        # 从工作范围中提取
        for scope in analysis.work_scope:
            project_keywords.add(scope.lower())

        # 计算匹配
        matched = []
        for hk in highlight_keywords:
            hk_lower = hk.lower()
            for pk in project_keywords:
                if hk_lower in pk or pk in hk_lower:
                    matched.append(hk)
                    break

        if not matched:
            return 0.0, []

        return len(matched) / len(highlight_keywords), matched

    def _score_pain_point_match(
        self,
        highlight: dict,
        analysis: ProjectAnalysis
    ) -> float:
        """计算痛点相关性得分"""
        highlight_name = highlight.get('name', '').lower()
        highlight_keywords = [k.lower() for k in highlight.get('keywords', [])]

        score = 0.0
        total = len(analysis.pain_points) if analysis.pain_points else 1

        for pain_point in analysis.pain_points:
            pp_lower = pain_point.lower()

            # Analytics/Data 项目解决数据相关痛点
            if 'analytics' in highlight_name or 'data' in highlight_keywords:
                if any(kw in pp_lower for kw in ['data', 'complex', 'metrics']):
                    score += 1

            # Enterprise 项目解决规模化痛点
            if any(kw in highlight_keywords for kw in ['enterprise', 'cloud', 'b2b']):
                if any(kw in pp_lower for kw in ['scaling', 'enterprise', 'teams']):
                    score += 1

            # Design System 解决一致性痛点
            if 'console' in highlight_name or 'admin' in highlight_keywords:
                if 'consistency' in pp_lower or 'design system' in pp_lower:
                    score += 1

        return min(score / total, 1.0)

    def _score_industry_match(
        self,
        highlight: dict,
        analysis: ProjectAnalysis
    ) -> float:
        """计算行业相关性得分"""
        highlight_keywords = [k.lower() for k in highlight.get('keywords', [])]
        industry = analysis.industry.lower()

        # 直接行业匹配
        industry_keyword_map = {
            'fintech': ['billing', 'fintech', 'cost', 'financial'],
            'finance': ['billing', 'fintech', 'cost', 'financial'],
            'saas': ['saas', 'b2b', 'enterprise', 'cloud'],
            'b2b': ['b2b', 'enterprise', 'management'],
            'analytics': ['analytics', 'data', 'metrics', 'dashboard'],
            'ecommerce': ['merchant', 'commerce', 'store', 'shop'],
            'retail': ['merchant', 'commerce', 'store', 'shop'],
            'mobile': ['mobile', 'app', 'ios', 'android'],
            'consumer': ['consumer', 'mobile', 'app'],
        }

        for ind_key, keywords in industry_keyword_map.items():
            if ind_key in industry:
                matches = sum(1 for k in keywords if k in highlight_keywords)
                if matches > 0:
                    return min(matches / len(keywords) * 2, 1.0)

        return 0.0

    def _score_stage_match(
        self,
        highlight: dict,
        analysis: ProjectAnalysis
    ) -> float:
        """计算项目阶段匹配得分"""
        # 简单的阶段匹配逻辑
        if analysis.project_stage == ProjectStage.REDESIGN:
            # 有过大规模重设计经验
            if 'analytics' in highlight.get('name', '').lower():
                return 1.0

        if analysis.project_stage == ProjectStage.GREENFIELD:
            # 有从0到1经验
            if 'matchbox' in highlight.get('name', '').lower():
                return 1.0

        return 0.3  # 基础分

    def _extract_relevant_metrics(
        self,
        highlight: dict,
        analysis: ProjectAnalysis
    ) -> List[str]:
        """提取与项目相关的指标"""
        metrics = []
        result = highlight.get('result_en', highlight.get('result', ''))

        # 提取数字指标
        number_patterns = [
            r'[\d,]+\+?\s*(?:apps?|users?|merchants?|million|providers?)',
            r'top\s*\d+',
            r'[\d,]+\+?\s*integrated',
        ]

        for pattern in number_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            metrics.extend(matches)

        # 如果没有提取到，返回整个结果
        if not metrics and result:
            metrics = [result]

        return metrics[:3]  # 限制数量

    def _get_pitch_angle(self, highlight: dict) -> PitchAngle:
        """获取成就对应的推销角度"""
        # 如果已定义
        if 'pitch_angle' in highlight:
            angle = highlight['pitch_angle']
            if isinstance(angle, PitchAngle):
                return angle
            try:
                return PitchAngle(angle)
            except ValueError:
                pass

        # 基于名称推断
        name = highlight.get('name', '').lower()

        if 'analytics' in name:
            return PitchAngle.DATA_VISUALIZATION
        elif 'business connect' in name or 'merchant' in name:
            return PitchAngle.MERCHANT_PLATFORM
        elif 'cloud' in name or 'billing' in name:
            return PitchAngle.ENTERPRISE_SYSTEM
        elif 'console' in name or 'admin' in name:
            return PitchAngle.ENTERPRISE_SYSTEM
        elif 'matchbox' in name or 'app' in name:
            return PitchAngle.MOBILE_CONSUMER

        return PitchAngle.GENERAL

    def _determine_primary_angle(
        self,
        achievements: List[RelevantAchievement],
        analysis: ProjectAnalysis
    ) -> PitchAngle:
        """确定主要推销角度"""
        if not achievements:
            return PitchAngle.GENERAL

        # 使用最相关成就的角度
        top = achievements[0]

        # 根据项目需求调整
        needs_lower = ' '.join(analysis.technical_needs).lower()

        if 'dashboard' in needs_lower or 'analytics' in needs_lower:
            return PitchAngle.DATA_VISUALIZATION

        if 'b2b' in needs_lower or 'enterprise' in needs_lower:
            return PitchAngle.ENTERPRISE_SYSTEM

        if 'design system' in needs_lower:
            return PitchAngle.DESIGN_SYSTEM

        return top.pitch_angle

    def _combine_metrics(
        self,
        achievements: List[RelevantAchievement]
    ) -> List[str]:
        """合并多个成就的指标"""
        all_metrics = []
        seen = set()

        for achievement in achievements:
            for metric in achievement.relevant_metrics:
                if metric not in seen:
                    all_metrics.append(metric)
                    seen.add(metric)

        return all_metrics[:5]  # 限制总数

    def _generate_summary(
        self,
        achievements: List[RelevantAchievement],
        analysis: ProjectAnalysis
    ) -> str:
        """生成匹配摘要"""
        if not achievements:
            return "No strong matches found, using general senior designer positioning."

        top = achievements[0]
        summary_parts = [
            f"Best match: {top.project_name} (score: {top.relevance_score:.2f})"
        ]

        if top.match_reasons:
            summary_parts.append(f"Reasons: {'; '.join(top.match_reasons)}")

        if len(achievements) > 1:
            other_names = [a.project_name for a in achievements[1:]]
            summary_parts.append(f"Also relevant: {', '.join(other_names)}")

        return ' | '.join(summary_parts)


# ============================================
# Convenience Functions
# ============================================

def match_achievements(
    analysis: ProjectAnalysis,
    user_profile: dict = None
) -> MatchResult:
    """快速匹配成就"""
    matcher = AchievementMatcher(user_profile)
    return matcher.match(analysis)


def get_best_achievement(
    analysis: ProjectAnalysis,
    user_profile: dict = None
) -> Optional[RelevantAchievement]:
    """获取最佳匹配成就"""
    result = match_achievements(analysis, user_profile)
    return result.top_achievement


# ============================================
# CLI Entry Point
# ============================================

def main():
    """命令行测试入口"""
    from .project_analyzer import ProjectRequirementsAnalyzer

    # 测试项目
    test_project = {
        'id': 'test-1',
        'client': 'TechStartup Inc',
        'title': 'Senior UX Designer for SaaS Dashboard',
        'industry': 'SaaS',
        'requirements': '''
        We need an experienced UX designer for our analytics dashboard.
        The product needs to handle complex data visualization.
        Enterprise clients require high-quality design.
        ''',
        'work_scope': ['Dashboard Design', 'Data Visualization'],
    }

    # 分析项目
    analyzer = ProjectRequirementsAnalyzer()
    analysis = analyzer.analyze(test_project)

    # 匹配成就
    matcher = AchievementMatcher()
    result = matcher.match(analysis)

    print("\n" + "=" * 60)
    print("ACHIEVEMENT MATCHING RESULT")
    print("=" * 60)

    if result.top_achievement:
        top = result.top_achievement
        print(f"\nBest Match: {top.project_name}")
        print(f"Relevance Score: {top.relevance_score:.2f}")
        print(f"Pitch Angle: {top.pitch_angle.value}")
        print(f"\nMatch Reasons:")
        for reason in top.match_reasons:
            print(f"  • {reason}")
        print(f"\nRelevant Metrics:")
        for metric in top.relevant_metrics:
            print(f"  • {metric}")

    if len(result.all_achievements) > 1:
        print(f"\nOther Relevant Achievements:")
        for a in result.all_achievements[1:]:
            print(f"  • {a.project_name} (score: {a.relevance_score:.2f})")

    print(f"\nMatch Summary: {result.match_summary}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
