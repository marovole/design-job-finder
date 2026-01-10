#!/usr/bin/env python3
"""
Realtime Verifier Module
实时验证协调器：统一接口整合邮箱、URL、项目活跃度验证

Features:
- Unified verification interface
- Parallel async validation
- Configurable verification levels
- Real-time validation during data collection
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime
import logging

# Handle both package and standalone imports
try:
    from .enhanced_email_validator import (
        EnhancedEmailValidator,
        EmailValidationResult,
        ValidationStatus as EmailValidationStatus
    )
    from .smart_url_validator import (
        SmartURLValidator,
        URLValidationResult,
        URLValidationStatus,
        validate_url_format
    )
except ImportError:
    from enhanced_email_validator import (
        EnhancedEmailValidator,
        EmailValidationResult,
        ValidationStatus as EmailValidationStatus
    )
    from smart_url_validator import (
        SmartURLValidator,
        URLValidationResult,
        URLValidationStatus,
        validate_url_format
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OverallValidationStatus(Enum):
    """综合验证状态"""
    VALID = "valid"            # 所有验证通过
    PARTIAL = "partial"        # 部分验证通过
    INVALID = "invalid"        # 关键验证失败
    UNKNOWN = "unknown"        # 无法确定


class VerificationLevel(Enum):
    """验证级别"""
    QUICK = "quick"            # 仅格式验证
    STANDARD = "standard"      # 格式 + MX + 一次性检测
    FULL = "full"              # 包含 HTTP 可达性和 SMTP


@dataclass
class VerificationConfig:
    """验证配置"""
    level: VerificationLevel = VerificationLevel.STANDARD

    # 邮箱验证配置
    email_check_format: bool = True
    email_check_mx: bool = True
    email_check_disposable: bool = True
    email_check_smtp: bool = False  # 较慢，默认关闭

    # URL 验证配置
    url_check_format: bool = True
    url_check_accessibility: bool = False  # 默认关闭
    url_timeout: int = 5

    # 活跃度检测配置
    check_activity: bool = False  # 需要 Exa API

    # 过滤配置
    filter_invalid: bool = False  # 是否过滤无效项目
    require_email: bool = False   # 是否要求有邮箱
    require_contact: bool = True  # 是否要求有任意联系方式

    @classmethod
    def quick(cls) -> 'VerificationConfig':
        """快速验证配置"""
        return cls(
            level=VerificationLevel.QUICK,
            email_check_mx=False,
            url_check_accessibility=False
        )

    @classmethod
    def standard(cls) -> 'VerificationConfig':
        """标准验证配置"""
        return cls(
            level=VerificationLevel.STANDARD,
            email_check_mx=True,
            url_check_accessibility=False
        )

    @classmethod
    def full(cls) -> 'VerificationConfig':
        """完整验证配置"""
        return cls(
            level=VerificationLevel.FULL,
            email_check_mx=True,
            email_check_smtp=True,
            url_check_accessibility=True,
            check_activity=True
        )


@dataclass
class ProjectVerificationResult:
    """项目验证结果"""
    project_id: str
    status: OverallValidationStatus
    email_result: Optional[EmailValidationResult] = None
    url_results: Dict[str, URLValidationResult] = field(default_factory=dict)
    activity_status: Optional[str] = None
    validation_notes: List[str] = field(default_factory=list)
    verified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'project_id': self.project_id,
            'status': self.status.value,
            'email_result': self.email_result.to_dict() if self.email_result else None,
            'url_results': {k: v.to_dict() for k, v in self.url_results.items()},
            'activity_status': self.activity_status,
            'validation_notes': self.validation_notes,
            'verified_at': self.verified_at,
            'details': self.details
        }

    @property
    def is_valid(self) -> bool:
        return self.status == OverallValidationStatus.VALID

    @property
    def has_valid_contact(self) -> bool:
        """是否有有效的联系方式"""
        # 有效邮箱
        if self.email_result and self.email_result.is_valid:
            return True
        # 有效 LinkedIn
        linkedin = self.url_results.get('linkedin')
        if linkedin and linkedin.is_valid:
            return True
        return False


class RealtimeVerifier:
    """
    实时验证器

    在数据收集阶段即时验证项目信息的有效性
    """

    def __init__(self, config: VerificationConfig = None):
        self.config = config or VerificationConfig.standard()

        # 初始化子验证器
        self.email_validator = EnhancedEmailValidator(
            check_mx=self.config.email_check_mx,
            check_disposable=self.config.email_check_disposable,
            check_smtp=self.config.email_check_smtp
        )

        self.url_validator = SmartURLValidator(
            check_accessibility=self.config.url_check_accessibility,
            timeout=self.config.url_timeout
        )

    async def verify_project(self, project: dict) -> ProjectVerificationResult:
        """
        验证单个项目

        Args:
            project: 项目数据字典

        Returns:
            ProjectVerificationResult: 验证结果
        """
        project_id = project.get('id', project.get('client', 'unknown'))
        validation_notes = []
        details = {}

        # 并行执行所有验证
        email = project.get('email', '')
        urls = {
            'website': project.get('website', ''),
            'linkedin': project.get('linkedin', ''),
            'platform_link': project.get('platform_link', '')
        }

        # 创建验证任务
        tasks = []

        # 邮箱验证
        if email and self.config.email_check_format:
            tasks.append(('email', self._verify_email(email)))
        else:
            email_result = None
            if self.config.require_email:
                validation_notes.append("邮箱为空")

        # URL 验证
        url_tasks = []
        for field_name, url in urls.items():
            if url:
                url_tasks.append((field_name, self._verify_url(url, field_name)))

        tasks.extend(url_tasks)

        # 执行所有验证任务
        email_result = None
        url_results = {}

        if tasks:
            results = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )

            for i, (task_name, _) in enumerate(tasks):
                result = results[i]

                if isinstance(result, Exception):
                    logger.error(f"Verification error for {task_name}: {result}")
                    continue

                if task_name == 'email':
                    email_result = result
                    if not result.is_valid:
                        validation_notes.append(result.message)
                else:
                    url_results[task_name] = result
                    if result.status == URLValidationStatus.INVALID:
                        validation_notes.append(result.message)

        # 计算综合状态
        overall_status = self._calculate_overall_status(
            email_result, url_results, validation_notes
        )

        return ProjectVerificationResult(
            project_id=project_id,
            status=overall_status,
            email_result=email_result,
            url_results=url_results,
            validation_notes=validation_notes,
            details=details
        )

    async def _verify_email(self, email: str) -> EmailValidationResult:
        """验证邮箱"""
        return await self.email_validator.validate_async(email)

    async def _verify_url(self, url: str, field_name: str) -> URLValidationResult:
        """验证 URL"""
        if self.config.url_check_accessibility:
            return await self.url_validator.validate(url, field_name)
        else:
            return self.url_validator.validate_format(url, field_name)

    def _calculate_overall_status(
        self,
        email_result: Optional[EmailValidationResult],
        url_results: Dict[str, URLValidationResult],
        validation_notes: List[str]
    ) -> OverallValidationStatus:
        """
        计算综合验证状态

        策略：
        - 如果有有效邮箱或有效 LinkedIn，视为有效
        - 如果全部无效，视为无效
        - 其他情况视为部分有效
        """
        valid_count = 0
        invalid_count = 0
        total_count = 0

        # 邮箱
        if email_result:
            total_count += 1
            if email_result.is_valid:
                valid_count += 1
            elif email_result.is_invalid:
                invalid_count += 1

        # URLs
        for result in url_results.values():
            if result.url:  # 只计算非空 URL
                total_count += 1
                if result.is_valid:
                    valid_count += 1
                elif result.is_invalid:
                    invalid_count += 1

        # 判断状态
        if total_count == 0:
            return OverallValidationStatus.INVALID

        if valid_count == total_count:
            return OverallValidationStatus.VALID

        if invalid_count == total_count:
            return OverallValidationStatus.INVALID

        # 检查是否有有效联系方式
        has_valid_contact = False
        if email_result and email_result.is_valid:
            has_valid_contact = True
        if url_results.get('linkedin') and url_results['linkedin'].is_valid:
            has_valid_contact = True

        if has_valid_contact:
            return OverallValidationStatus.PARTIAL

        return OverallValidationStatus.INVALID

    async def verify_batch(
        self,
        projects: List[dict],
        max_concurrent: int = 10,
        progress_callback: callable = None
    ) -> List[ProjectVerificationResult]:
        """
        批量验证项目

        Args:
            projects: 项目列表
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数 (current, total)

        Returns:
            验证结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        total = len(projects)

        async def verify_with_semaphore(
            project: dict, index: int
        ) -> ProjectVerificationResult:
            async with semaphore:
                result = await self.verify_project(project)
                if progress_callback:
                    progress_callback(index + 1, total)
                return result

        tasks = [
            verify_with_semaphore(project, i)
            for i, project in enumerate(projects)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch verification error: {result}")
                final_results.append(ProjectVerificationResult(
                    project_id=projects[i].get('id', str(i)),
                    status=OverallValidationStatus.UNKNOWN,
                    validation_notes=[f"验证出错: {str(result)[:50]}"]
                ))
            else:
                final_results.append(result)

        return final_results

    def verify_project_sync(self, project: dict) -> ProjectVerificationResult:
        """
        同步验证项目

        用于不需要异步的场景
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.verify_project(project))

    def verify_batch_sync(
        self,
        projects: List[dict],
        max_concurrent: int = 10,
        progress_callback: callable = None
    ) -> List[ProjectVerificationResult]:
        """
        同步批量验证项目
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.verify_batch(projects, max_concurrent, progress_callback)
        )


# ============================================
# Convenience Functions
# ============================================

def quick_verify(project: dict) -> ProjectVerificationResult:
    """快速验证项目（仅格式检查）"""
    verifier = RealtimeVerifier(VerificationConfig.quick())
    return verifier.verify_project_sync(project)


def standard_verify(project: dict) -> ProjectVerificationResult:
    """标准验证项目"""
    verifier = RealtimeVerifier(VerificationConfig.standard())
    return verifier.verify_project_sync(project)


async def full_verify_async(project: dict) -> ProjectVerificationResult:
    """完整验证项目（异步）"""
    verifier = RealtimeVerifier(VerificationConfig.full())
    return await verifier.verify_project(project)


def apply_verification_to_project(
    project: dict,
    verification_result: ProjectVerificationResult
) -> dict:
    """
    将验证结果应用到项目数据

    Args:
        project: 原始项目数据
        verification_result: 验证结果

    Returns:
        带验证信息的项目数据
    """
    result = project.copy()

    # 添加验证状态
    result['is_valid'] = verification_result.is_valid
    result['validation_status'] = verification_result.status.value
    result['validation_notes'] = verification_result.validation_notes
    result['validated_at'] = verification_result.verified_at

    # 添加详细验证结果
    if verification_result.email_result:
        result['email_validation'] = verification_result.email_result.to_dict()

    if verification_result.url_results:
        result['url_validations'] = {
            k: v.to_dict() for k, v in verification_result.url_results.items()
        }

    # 添加联系方式有效性标记
    result['has_valid_contact'] = verification_result.has_valid_contact

    return result


def filter_valid_projects(
    projects: List[dict],
    verification_results: List[ProjectVerificationResult]
) -> Tuple[List[dict], List[dict]]:
    """
    根据验证结果过滤项目

    Args:
        projects: 项目列表
        verification_results: 验证结果列表

    Returns:
        (有效项目列表, 无效项目列表)
    """
    valid_projects = []
    invalid_projects = []

    for project, result in zip(projects, verification_results):
        enhanced_project = apply_verification_to_project(project, result)

        if result.status in [
            OverallValidationStatus.VALID,
            OverallValidationStatus.PARTIAL
        ] and result.has_valid_contact:
            valid_projects.append(enhanced_project)
        else:
            invalid_projects.append(enhanced_project)

    return valid_projects, invalid_projects


# ============================================
# CLI Entry Point
# ============================================

def main():
    """命令行测试入口"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Realtime Project Verifier')
    parser.add_argument('--input', '-i', help='Input JSON file with projects')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--level', choices=['quick', 'standard', 'full'],
                       default='standard', help='Verification level')

    args = parser.parse_args()

    # 配置
    config_map = {
        'quick': VerificationConfig.quick(),
        'standard': VerificationConfig.standard(),
        'full': VerificationConfig.full()
    }
    config = config_map[args.level]

    # 加载数据
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
            projects = data if isinstance(data, list) else data.get('projects', [])
    else:
        # 测试数据
        projects = [
            {
                'id': 'test-1',
                'client': 'Test Company',
                'email': 'test@example.com',
                'linkedin': 'https://linkedin.com/company/test',
                'website': 'https://example.com'
            }
        ]

    print(f"Verifying {len(projects)} projects with level: {args.level}")

    # 验证
    verifier = RealtimeVerifier(config)

    def progress(current, total):
        print(f"  [{current}/{total}]", end='\r')

    results = verifier.verify_batch_sync(projects, progress_callback=progress)

    # 统计
    valid_count = sum(1 for r in results if r.is_valid)
    partial_count = sum(1 for r in results
                       if r.status == OverallValidationStatus.PARTIAL)
    invalid_count = sum(1 for r in results
                       if r.status == OverallValidationStatus.INVALID)

    print(f"\n\nResults:")
    print(f"  Valid: {valid_count}")
    print(f"  Partial: {partial_count}")
    print(f"  Invalid: {invalid_count}")

    # 保存结果
    if args.output:
        output_data = {
            'verified_at': datetime.now().isoformat(),
            'level': args.level,
            'total': len(projects),
            'valid': valid_count,
            'partial': partial_count,
            'invalid': invalid_count,
            'results': [r.to_dict() for r in results]
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
