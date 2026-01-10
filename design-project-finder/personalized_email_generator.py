#!/usr/bin/env python3
"""
Personalized Email Generator Module
个性化邮件生成：基于项目分析和成就匹配生成针对性邮件

Features:
- Deep personalization based on project analysis
- Pain point addressing
- Achievement-based social proof
- Multiple pitch angles
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import yaml
import logging

# Handle both package and standalone imports
try:
    from .project_analyzer import (
        ProjectRequirementsAnalyzer,
        ProjectAnalysis,
        ProjectStage,
        UrgencyLevel
    )
    from .achievement_matcher import (
        AchievementMatcher,
        MatchResult,
        RelevantAchievement,
        PitchAngle
    )
except ImportError:
    from project_analyzer import (
        ProjectRequirementsAnalyzer,
        ProjectAnalysis,
        ProjectStage,
        UrgencyLevel
    )
    from achievement_matcher import (
        AchievementMatcher,
        MatchResult,
        RelevantAchievement,
        PitchAngle
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PersonalizedEmail:
    """个性化邮件"""
    # 基本信息
    project_id: str = ""
    client_name: str = ""

    # 邮件内容
    subject_lines: List[str] = field(default_factory=list)
    opening: str = ""
    value_proposition: str = ""
    social_proof: str = ""
    call_to_action: str = ""
    signature: str = ""

    # 完整邮件
    full_email: str = ""

    # 元数据
    pitch_angle: str = ""
    matched_achievement: str = ""
    relevance_score: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'project_id': self.project_id,
            'client_name': self.client_name,
            'subject_lines': self.subject_lines,
            'opening': self.opening,
            'value_proposition': self.value_proposition,
            'social_proof': self.social_proof,
            'call_to_action': self.call_to_action,
            'signature': self.signature,
            'full_email': self.full_email,
            'pitch_angle': self.pitch_angle,
            'matched_achievement': self.matched_achievement,
            'relevance_score': self.relevance_score,
            'generated_at': self.generated_at
        }

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"# Email for {self.client_name}",
            "",
            "## Subject Line Options",
        ]

        for i, subject in enumerate(self.subject_lines, 1):
            lines.append(f"{i}. {subject}")

        lines.extend([
            "",
            "---",
            "",
            "## Email Body",
            "",
            self.full_email,
            "",
            "---",
            "",
            "## Metadata",
            f"- **Pitch Angle**: {self.pitch_angle}",
            f"- **Matched Achievement**: {self.matched_achievement}",
            f"- **Relevance Score**: {self.relevance_score:.2f}",
            f"- **Generated**: {self.generated_at}",
        ])

        return "\n".join(lines)


# ============================================
# Default User Profile Configuration
# ============================================

DEFAULT_USER_CONFIG = {
    'name': 'Rong Huang',
    'name_cn': '黄蓉',
    'email': 'hueshadow989@gmail.com',
    'website': 'https://hueshadow.com',
    'role': 'Senior UX Designer',
    'years_experience': 10,
    'company': 'Huawei',
    'company_years': 6,
}

DEFAULT_SIGNATURE = """Best regards,
Rong Huang (黄蓉)
Senior UX Designer | Product Manager

Portfolio: https://hueshadow.com
Email: hueshadow989@gmail.com"""


class PersonalizedEmailGenerator:
    """
    个性化邮件生成器

    基于项目分析和成就匹配生成高度个性化的邮件
    """

    def __init__(self, user_profile: dict = None):
        self.user_profile = user_profile or self._load_user_profile()
        self.user_config = self._extract_user_config()

        # 初始化分析器和匹配器
        self.analyzer = ProjectRequirementsAnalyzer(self.user_profile)
        self.matcher = AchievementMatcher(self.user_profile)

    def _load_user_profile(self) -> dict:
        """加载用户配置"""
        config_path = Path(__file__).parent / "user_profile.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load user profile: {e}")
        return {}

    def _extract_user_config(self) -> dict:
        """提取用户基本配置"""
        config = DEFAULT_USER_CONFIG.copy()

        if self.user_profile:
            config.update({
                'name': self.user_profile.get('name_en', config['name']),
                'name_cn': self.user_profile.get('name', config['name_cn']),
                'email': self.user_profile.get('email', config['email']),
                'website': self.user_profile.get('website', config['website']),
                'role': self.user_profile.get('role_en', config['role']),
                'years_experience': self.user_profile.get('years_experience', config['years_experience']),
            })

        return config

    def generate(self, project: dict) -> PersonalizedEmail:
        """
        为项目生成个性化邮件

        Args:
            project: 项目数据字典

        Returns:
            PersonalizedEmail: 生成的邮件
        """
        # Step 1: 深度分析项目
        analysis = self.analyzer.analyze(project)

        # Step 2: 匹配成就
        match_result = self.matcher.match(analysis)

        # Step 3: 生成个性化内容
        email = PersonalizedEmail(
            project_id=analysis.project_id,
            client_name=analysis.client_name or project.get('client', 'Team')
        )

        # 生成各个部分
        email.subject_lines = self._generate_subject_lines(project, analysis, match_result)
        email.opening = self._generate_opening(project, analysis, match_result)
        email.value_proposition = self._generate_value_proposition(analysis, match_result)
        email.social_proof = self._generate_social_proof(match_result)
        email.call_to_action = self._generate_cta(project, analysis)
        email.signature = self._get_signature()

        # 组装完整邮件
        email.full_email = self._assemble_email(email)

        # 添加元数据
        email.pitch_angle = match_result.primary_pitch_angle.value
        if match_result.top_achievement:
            email.matched_achievement = match_result.top_achievement.project_name
            email.relevance_score = match_result.top_achievement.relevance_score

        return email

    def _generate_subject_lines(
        self,
        project: dict,
        analysis: ProjectAnalysis,
        match_result: MatchResult
    ) -> List[str]:
        """生成多个主题行选项"""
        client = analysis.client_name or project.get('client', 'your team')
        title = analysis.project_title or project.get('title', 'your project')

        subjects = []

        # 基于匹配角度的主题
        if match_result.primary_pitch_angle == PitchAngle.DATA_VISUALIZATION:
            subjects.append(
                f"Analytics Dashboard Expert - 21,000+ Apps Experience"
            )
            subjects.append(
                f"Re: {title[:30]}... - Huawei Analytics Lead Designer"
            )

        elif match_result.primary_pitch_angle == PitchAngle.ENTERPRISE_SYSTEM:
            subjects.append(
                f"Enterprise UX Specialist - 6 Years at Huawei"
            )
            subjects.append(
                f"Re: {title[:30]}... - B2B Platform Design Expert"
            )

        elif match_result.primary_pitch_angle == PitchAngle.MERCHANT_PLATFORM:
            subjects.append(
                f"5.94M Merchants Platform Experience - UX Designer"
            )

        # 通用主题
        subjects.append(
            f"Senior UX Designer | 10+ Years Experience | {client}"
        )
        subjects.append(
            f"Application: {title[:40]}..."
        )

        return subjects[:4]  # 最多4个

    def _generate_opening(
        self,
        project: dict,
        analysis: ProjectAnalysis,
        match_result: MatchResult
    ) -> str:
        """
        生成个性化开场白

        策略：引用项目细节 + 最相关成就
        """
        client = analysis.client_name or project.get('client', 'Team')
        title = analysis.project_title or project.get('title', 'your project')
        platform = analysis.platform or project.get('platform', '')

        top_achievement = match_result.top_achievement

        # 根据推销角度生成开场
        if match_result.primary_pitch_angle == PitchAngle.DATA_VISUALIZATION:
            if top_achievement and 'analytics' in top_achievement.project_name.lower():
                metrics = top_achievement.relevant_metrics
                metric_str = metrics[0] if metrics else '21,000+ apps globally'
                return f"""Hi {client},

I noticed your {title} posting{f' on {platform}' if platform else ''}—the focus on data visualization and dashboards immediately caught my attention.

During my 6 years at Huawei, I led the UX design for HUAWEI Analytics, a platform benchmarked against Google Analytics that now serves {metric_str}. Translating complex data into intuitive interfaces is exactly what I do best."""

        elif match_result.primary_pitch_angle == PitchAngle.ENTERPRISE_SYSTEM:
            return f"""Hi {client},

Your {title} role immediately resonated with my background.

At Huawei, I've spent 6 years designing enterprise-scale systems—from cloud billing platforms to developer consoles. I understand the unique challenges of enterprise UX: balancing power users with onboarding, maintaining consistency at scale, and navigating complex workflows."""

        elif match_result.primary_pitch_angle == PitchAngle.MERCHANT_PLATFORM:
            return f"""Hi {client},

I came across your {title} posting{f' on {platform}' if platform else ''} and it resonated strongly with my experience.

I led the design for Business Connect (Huawei's answer to Google My Business), which now serves 5.94 million merchants. Your project aligns closely with my expertise in merchant-facing platforms."""

        # 通用开场
        return f"""Hi {client},

I came across your {title} posting{f' on {platform}' if platform else ''} and was impressed by the project scope.

With 10+ years in UX design and product management, including 6 years leading enterprise product design at Huawei, I bring deep expertise in exactly the type of work you're describing."""

    def _generate_value_proposition(
        self,
        analysis: ProjectAnalysis,
        match_result: MatchResult
    ) -> str:
        """
        生成价值主张

        策略：针对项目痛点的解决方案
        """
        pain_points = analysis.pain_points
        value_statements = []

        for pain_point in pain_points[:3]:  # 最多3个
            pp_lower = pain_point.lower()

            if 'scaling' in pp_lower or 'teams' in pp_lower:
                value_statements.append(
                    "I've built design systems that scale across multiple product teams—"
                    "reducing design debt and accelerating development velocity."
                )

            elif 'data' in pp_lower or 'complex' in pp_lower:
                value_statements.append(
                    "I specialize in making complex data accessible. My work on HUAWEI Analytics "
                    "involved designing dashboards that serve both novice marketers and data analysts—"
                    "a balance I'm proud of."
                )

            elif 'accessibility' in pp_lower or 'wcag' in pp_lower:
                value_statements.append(
                    "Accessibility is a core competency, not an afterthought. I've led WCAG 2.1 AA "
                    "compliance initiatives and believe great UX should be inclusive by design."
                )

            elif 'compliance' in pp_lower or 'regulatory' in pp_lower:
                value_statements.append(
                    "I understand the constraints of regulated industries. My enterprise experience "
                    "includes designing within strict compliance frameworks while still delivering "
                    "exceptional user experiences."
                )

            elif 'onboarding' in pp_lower or 'activation' in pp_lower:
                value_statements.append(
                    "User onboarding is where first impressions are made. I've designed flows "
                    "that reduce time-to-value and increase feature adoption rates."
                )

            elif 'consistency' in pp_lower or 'design system' in pp_lower:
                value_statements.append(
                    "Design consistency at scale requires systematic thinking. I've developed "
                    "component libraries and design systems that ensure coherent experiences "
                    "across multiple products."
                )

        # 如果没有匹配的痛点，添加通用价值主张
        if not value_statements:
            value_statements.append(
                "My experience spans B2B/SaaS products, design systems, and complex enterprise "
                "workflows—exactly the foundation your project needs."
            )

        return "\n\n".join(value_statements)

    def _generate_social_proof(self, match_result: MatchResult) -> str:
        """
        生成社会证明

        策略：具体数据指标
        """
        metrics = match_result.combined_metrics

        if not metrics:
            return ""

        proof_parts = ["Key achievements relevant to your project:"]

        for metric in metrics[:3]:
            proof_parts.append(f"• {metric}")

        return "\n".join(proof_parts)

    def _generate_cta(
        self,
        project: dict,
        analysis: ProjectAnalysis
    ) -> str:
        """
        生成行动号召

        策略：根据项目类型定制
        """
        work_type = project.get('work_type', '').lower()

        # 检测是否是远程/兼职
        is_remote = any(kw in work_type for kw in ['remote', 'freelance', 'part-time', 'contract'])

        if is_remote:
            return """I'm based in China (UTC+8) and prefer asynchronous communication via email. Happy to discuss project details, share relevant case studies, or answer any questions you might have.

Looking forward to learning more about your project."""

        # 根据紧急程度
        if analysis.urgency == UrgencyLevel.HIGH:
            return """I'm available to start immediately and can adapt to your timeline. Would love to discuss how I can contribute to your project's success.

Please feel free to reach out at your earliest convenience."""

        # 默认 CTA
        return """I'd welcome the opportunity to discuss how my experience could contribute to your project. Happy to share portfolio pieces, case studies, or schedule a brief call at your convenience.

Looking forward to connecting."""

    def _get_signature(self) -> str:
        """获取签名"""
        # 尝试从用户配置加载
        if self.user_profile.get('email_signature'):
            return self.user_profile['email_signature']

        return DEFAULT_SIGNATURE

    def _assemble_email(self, email: PersonalizedEmail) -> str:
        """组装完整邮件"""
        parts = [email.opening]

        if email.value_proposition:
            parts.append(email.value_proposition)

        if email.social_proof:
            parts.append(email.social_proof)

        if email.call_to_action:
            parts.append(email.call_to_action)

        parts.append(email.signature)

        return "\n\n".join(parts)

    def generate_batch(self, projects: List[dict]) -> List[PersonalizedEmail]:
        """批量生成邮件"""
        return [self.generate(project) for project in projects]


# ============================================
# Convenience Functions
# ============================================

def generate_email(project: dict, user_profile: dict = None) -> PersonalizedEmail:
    """快速生成个性化邮件"""
    generator = PersonalizedEmailGenerator(user_profile)
    return generator.generate(project)


def generate_email_markdown(project: dict, user_profile: dict = None) -> str:
    """生成邮件并返回 Markdown 格式"""
    email = generate_email(project, user_profile)
    return email.to_markdown()


def save_email_to_file(
    email: PersonalizedEmail,
    output_dir: Path,
    filename: str = None
) -> Path:
    """保存邮件到文件"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        safe_client = "".join(c if c.isalnum() else "_" for c in email.client_name)
        filename = f"{email.project_id}_{safe_client}_email.md"

    file_path = output_dir / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(email.to_markdown())

    return file_path


# ============================================
# CLI Entry Point
# ============================================

def main():
    """命令行测试入口"""
    import json

    # 测试项目
    test_project = {
        'id': 'test-001',
        'client': 'DataViz Solutions',
        'title': 'Senior UX Designer for Analytics Dashboard',
        'industry': 'SaaS',
        'platform': 'LinkedIn',
        'requirements': '''
        We're looking for an experienced UX designer to redesign our analytics dashboard.
        The product serves enterprise clients with complex data needs.
        Key requirements:
        - Data visualization expertise
        - Experience with enterprise software
        - Design system development
        - WCAG accessibility compliance
        ''',
        'work_scope': ['Dashboard Design', 'Data Visualization', 'Design System'],
        'work_type': 'Remote / Contract',
    }

    # 生成邮件
    generator = PersonalizedEmailGenerator()
    email = generator.generate(test_project)

    # 输出结果
    print("\n" + "=" * 60)
    print("PERSONALIZED EMAIL GENERATED")
    print("=" * 60)

    print("\n📧 SUBJECT LINE OPTIONS:")
    for i, subject in enumerate(email.subject_lines, 1):
        print(f"   {i}. {subject}")

    print("\n" + "-" * 60)
    print("📝 EMAIL BODY:")
    print("-" * 60)
    print(email.full_email)

    print("\n" + "-" * 60)
    print("📊 METADATA:")
    print(f"   Pitch Angle: {email.pitch_angle}")
    print(f"   Matched Achievement: {email.matched_achievement}")
    print(f"   Relevance Score: {email.relevance_score:.2f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
