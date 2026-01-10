"""
Design Project Finder Package
设计项目发现工具包

Modules:
- enhanced_email_validator: 多层邮箱验证
- smart_url_validator: 智能URL验证
- realtime_verifier: 实时验证协调器
- project_analyzer: 项目需求深度分析
- achievement_matcher: 用户成就智能匹配
- personalized_email_generator: 个性化邮件生成
"""

from .enhanced_email_validator import (
    EnhancedEmailValidator,
    EmailValidationResult,
    ValidationStatus,
    EmailType,
    quick_validate,
    full_validate,
)

from .smart_url_validator import (
    SmartURLValidator,
    URLValidationResult,
    URLValidationStatus,
    URLType,
    validate_url_format,
    validate_linkedin_url,
)

from .realtime_verifier import (
    RealtimeVerifier,
    VerificationConfig,
    VerificationLevel,
    ProjectVerificationResult,
    OverallValidationStatus,
    quick_verify,
    standard_verify,
    apply_verification_to_project,
    filter_valid_projects,
)

from .project_analyzer import (
    ProjectRequirementsAnalyzer,
    ProjectAnalysis,
    ProjectStage,
    UrgencyLevel,
    TeamSize,
    analyze_project,
    analyze_batch,
)

from .achievement_matcher import (
    AchievementMatcher,
    MatchResult,
    RelevantAchievement,
    PitchAngle,
    match_achievements,
    get_best_achievement,
)

from .personalized_email_generator import (
    PersonalizedEmailGenerator,
    PersonalizedEmail,
    generate_email,
    generate_email_markdown,
    save_email_to_file,
)

__all__ = [
    # Email Validator
    'EnhancedEmailValidator',
    'EmailValidationResult',
    'ValidationStatus',
    'EmailType',
    'quick_validate',
    'full_validate',

    # URL Validator
    'SmartURLValidator',
    'URLValidationResult',
    'URLValidationStatus',
    'URLType',
    'validate_url_format',
    'validate_linkedin_url',

    # Realtime Verifier
    'RealtimeVerifier',
    'VerificationConfig',
    'VerificationLevel',
    'ProjectVerificationResult',
    'OverallValidationStatus',
    'quick_verify',
    'standard_verify',
    'apply_verification_to_project',
    'filter_valid_projects',

    # Project Analyzer
    'ProjectRequirementsAnalyzer',
    'ProjectAnalysis',
    'ProjectStage',
    'UrgencyLevel',
    'TeamSize',
    'analyze_project',
    'analyze_batch',

    # Achievement Matcher
    'AchievementMatcher',
    'MatchResult',
    'RelevantAchievement',
    'PitchAngle',
    'match_achievements',
    'get_best_achievement',

    # Email Generator
    'PersonalizedEmailGenerator',
    'PersonalizedEmail',
    'generate_email',
    'generate_email_markdown',
    'save_email_to_file',
]

__version__ = '2.0.0'
