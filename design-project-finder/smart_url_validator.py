#!/usr/bin/env python3
"""
Smart URL Validator Module
智能URL验证：格式检查 → 平台专用验证 → HTTP可达性检测

Features:
- Async HTTP validation with timeout
- LinkedIn-specific URL pattern validation
- TTL caching to avoid duplicate requests
- Parallel batch validation
"""

import re
import asyncio
import aiohttp
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLValidationStatus(Enum):
    """URL验证状态"""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    REDIRECT = "redirect"  # 重定向到其他URL
    TIMEOUT = "timeout"


class URLType(Enum):
    """URL类型"""
    WEBSITE = "website"
    LINKEDIN_COMPANY = "linkedin_company"
    LINKEDIN_PERSON = "linkedin_person"
    LINKEDIN_JOB = "linkedin_job"
    PLATFORM_LINK = "platform_link"
    UPWORK = "upwork"
    TOPTAL = "toptal"
    DRIBBBLE = "dribbble"
    OTHER = "other"


@dataclass
class URLValidationResult:
    """URL验证结果"""
    url: str
    field_name: str
    status: URLValidationStatus
    message: str
    url_type: URLType = URLType.OTHER
    http_code: Optional[int] = None
    final_url: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'field_name': self.field_name,
            'status': self.status.value,
            'message': self.message,
            'url_type': self.url_type.value,
            'http_code': self.http_code,
            'final_url': self.final_url,
            'details': self.details
        }

    @property
    def is_valid(self) -> bool:
        return self.status == URLValidationStatus.VALID

    @property
    def is_invalid(self) -> bool:
        return self.status == URLValidationStatus.INVALID


# ============================================
# URL Cache
# ============================================

class URLCache:
    """URL 验证结果缓存"""
    def __init__(self, ttl_hours: int = 1):
        self._cache: Dict[str, Tuple[URLValidationResult, datetime]] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, url: str) -> Optional[URLValidationResult]:
        """获取缓存的验证结果"""
        if url in self._cache:
            result, cached_at = self._cache[url]
            if datetime.now() - cached_at < self._ttl:
                result.details['cached'] = True
                return result
            else:
                del self._cache[url]
        return None

    def set(self, url: str, result: URLValidationResult):
        """设置验证结果缓存"""
        self._cache[url] = (result, datetime.now())

    def clear(self):
        """清除缓存"""
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# Global URL cache
_url_cache = URLCache()


# ============================================
# URL Pattern Definitions
# ============================================

# LinkedIn URL patterns
LINKEDIN_PATTERNS = {
    'company': re.compile(
        r'^https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)/?.*$',
        re.IGNORECASE
    ),
    'person': re.compile(
        r'^https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?.*$',
        re.IGNORECASE
    ),
    'job': re.compile(
        r'^https?://(?:www\.)?linkedin\.com/jobs/view/(\d+)/?.*$',
        re.IGNORECASE
    ),
}

# Platform URL patterns
PLATFORM_PATTERNS = {
    'upwork': re.compile(r'^https?://(?:www\.)?upwork\.com/', re.IGNORECASE),
    'toptal': re.compile(r'^https?://(?:www\.)?toptal\.com/', re.IGNORECASE),
    'dribbble': re.compile(r'^https?://(?:www\.)?dribbble\.com/', re.IGNORECASE),
    'fiverr': re.compile(r'^https?://(?:www\.)?fiverr\.com/', re.IGNORECASE),
    'behance': re.compile(r'^https?://(?:www\.)?behance\.net/', re.IGNORECASE),
}


# ============================================
# URL Format Validation
# ============================================

def validate_url_format(url: str, field_name: str = "url") -> URLValidationResult:
    """
    验证 URL 基本格式

    检查：
    - 是否为空
    - 是否有协议前缀
    - 是否有有效的域名
    """
    if not url or not isinstance(url, str):
        return URLValidationResult(
            url=str(url) if url else "",
            field_name=field_name,
            status=URLValidationStatus.INVALID,
            message=f"{field_name} 为空或无效"
        )

    url = url.strip()

    # 检查协议
    if not url.lower().startswith(('http://', 'https://')):
        return URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.INVALID,
            message=f"{field_name} 缺少协议前缀 (http/https)"
        )

    # 解析 URL
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return URLValidationResult(
                url=url,
                field_name=field_name,
                status=URLValidationStatus.INVALID,
                message=f"{field_name} 域名无效"
            )

        # 确定 URL 类型
        url_type = detect_url_type(url)

        return URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.VALID,
            message=f"{field_name} 格式正确",
            url_type=url_type,
            details={'domain': parsed.netloc}
        )

    except Exception as e:
        return URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.INVALID,
            message=f"{field_name} 解析失败: {str(e)[:50]}"
        )


def detect_url_type(url: str) -> URLType:
    """检测 URL 类型"""
    url_lower = url.lower()

    # LinkedIn
    if 'linkedin.com' in url_lower:
        for pattern_name, pattern in LINKEDIN_PATTERNS.items():
            if pattern.match(url):
                if pattern_name == 'company':
                    return URLType.LINKEDIN_COMPANY
                elif pattern_name == 'person':
                    return URLType.LINKEDIN_PERSON
                elif pattern_name == 'job':
                    return URLType.LINKEDIN_JOB

    # 其他平台
    for platform_name, pattern in PLATFORM_PATTERNS.items():
        if pattern.match(url):
            if platform_name == 'upwork':
                return URLType.UPWORK
            elif platform_name == 'toptal':
                return URLType.TOPTAL
            elif platform_name == 'dribbble':
                return URLType.DRIBBBLE
            else:
                return URLType.PLATFORM_LINK

    return URLType.WEBSITE


# ============================================
# LinkedIn-Specific Validation
# ============================================

def validate_linkedin_url(url: str) -> URLValidationResult:
    """
    LinkedIn URL 专用验证

    检查：
    - URL 是否符合 LinkedIn 格式
    - 是否能提取有效的 ID/slug
    """
    field_name = "linkedin"

    if not url or 'linkedin.com' not in url.lower():
        return URLValidationResult(
            url=url or "",
            field_name=field_name,
            status=URLValidationStatus.INVALID,
            message="不是有效的 LinkedIn URL"
        )

    # 尝试匹配各种 LinkedIn URL 模式
    for pattern_name, pattern in LINKEDIN_PATTERNS.items():
        match = pattern.match(url)
        if match:
            identifier = match.group(1)
            url_type = {
                'company': URLType.LINKEDIN_COMPANY,
                'person': URLType.LINKEDIN_PERSON,
                'job': URLType.LINKEDIN_JOB
            }.get(pattern_name, URLType.OTHER)

            return URLValidationResult(
                url=url,
                field_name=field_name,
                status=URLValidationStatus.VALID,
                message=f"有效的 LinkedIn {pattern_name} URL",
                url_type=url_type,
                details={'identifier': identifier, 'type': pattern_name}
            )

    # 如果是 LinkedIn URL 但不符合已知模式
    return URLValidationResult(
        url=url,
        field_name=field_name,
        status=URLValidationStatus.UNKNOWN,
        message="LinkedIn URL 格式未知",
        details={'note': 'Unrecognized LinkedIn URL pattern'}
    )


# ============================================
# HTTP Accessibility Check
# ============================================

async def check_url_accessibility(
    url: str,
    field_name: str = "url",
    timeout: int = 5,
    follow_redirects: bool = True
) -> URLValidationResult:
    """
    异步检查 URL 可访问性

    使用 HTTP HEAD 请求检测 URL 是否可达
    """
    # 检查缓存
    cached = _url_cache.get(url)
    if cached:
        return cached

    # 格式验证
    format_result = validate_url_format(url, field_name)
    if format_result.status == URLValidationStatus.INVALID:
        return format_result

    url_type = format_result.url_type

    try:
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        connector = aiohttp.TCPConnector(ssl=False)  # 忽略 SSL 错误

        async with aiohttp.ClientSession(
            timeout=timeout_config,
            connector=connector
        ) as session:
            # 使用 HEAD 请求（更快）
            try:
                async with session.head(
                    url,
                    allow_redirects=follow_redirects,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                ) as response:
                    result = _process_http_response(
                        url, field_name, response, url_type
                    )
                    _url_cache.set(url, result)
                    return result

            except aiohttp.ClientResponseError:
                # HEAD 被拒绝，尝试 GET
                async with session.get(
                    url,
                    allow_redirects=follow_redirects,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                ) as response:
                    result = _process_http_response(
                        url, field_name, response, url_type
                    )
                    _url_cache.set(url, result)
                    return result

    except asyncio.TimeoutError:
        result = URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.TIMEOUT,
            message=f"{field_name} 访问超时 ({timeout}s)",
            url_type=url_type
        )
        _url_cache.set(url, result)
        return result

    except aiohttp.ClientError as e:
        error_type = type(e).__name__
        result = URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.INVALID,
            message=f"{field_name} 无法访问: {error_type}",
            url_type=url_type,
            details={'error': str(e)[:100]}
        )
        _url_cache.set(url, result)
        return result

    except Exception as e:
        result = URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.UNKNOWN,
            message=f"{field_name} 检测失败: {str(e)[:50]}",
            url_type=url_type
        )
        return result


def _process_http_response(
    url: str,
    field_name: str,
    response: aiohttp.ClientResponse,
    url_type: URLType
) -> URLValidationResult:
    """处理 HTTP 响应"""
    status_code = response.status
    final_url = str(response.url)

    # 成功响应
    if 200 <= status_code < 400:
        # 检查是否重定向到其他域
        original_domain = urlparse(url).netloc
        final_domain = urlparse(final_url).netloc

        if original_domain != final_domain:
            return URLValidationResult(
                url=url,
                field_name=field_name,
                status=URLValidationStatus.REDIRECT,
                message=f"{field_name} 重定向到 {final_domain}",
                url_type=url_type,
                http_code=status_code,
                final_url=final_url
            )

        return URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.VALID,
            message=f"{field_name} 可正常访问",
            url_type=url_type,
            http_code=status_code,
            final_url=final_url
        )

    # 客户端错误
    elif 400 <= status_code < 500:
        if status_code == 404:
            message = f"{field_name} 页面不存在 (404)"
        elif status_code == 403:
            message = f"{field_name} 访问被禁止 (403)"
        elif status_code == 401:
            message = f"{field_name} 需要认证 (401)"
        else:
            message = f"{field_name} 客户端错误 ({status_code})"

        return URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.INVALID,
            message=message,
            url_type=url_type,
            http_code=status_code
        )

    # 服务器错误
    else:
        return URLValidationResult(
            url=url,
            field_name=field_name,
            status=URLValidationStatus.UNKNOWN,
            message=f"{field_name} 服务器错误 ({status_code})",
            url_type=url_type,
            http_code=status_code
        )


# ============================================
# Main Validator Class
# ============================================

class SmartURLValidator:
    """
    智能 URL 验证器

    验证层级：
    - 格式验证（即时）
    - 平台专用验证（即时）
    - HTTP 可达性验证（异步）
    """

    def __init__(
        self,
        check_accessibility: bool = True,
        timeout: int = 5,
        use_cache: bool = True
    ):
        self.check_accessibility = check_accessibility
        self.timeout = timeout
        self.use_cache = use_cache

    def validate_format(self, url: str, field_name: str = "url") -> URLValidationResult:
        """仅验证格式（同步）"""
        return validate_url_format(url, field_name)

    def validate_linkedin(self, url: str) -> URLValidationResult:
        """验证 LinkedIn URL（同步）"""
        return validate_linkedin_url(url)

    async def validate(
        self,
        url: str,
        field_name: str = "url"
    ) -> URLValidationResult:
        """
        完整验证 URL（异步）

        包括格式验证和可达性检测
        """
        # 格式验证
        format_result = validate_url_format(url, field_name)
        if format_result.status == URLValidationStatus.INVALID:
            return format_result

        # LinkedIn 专用验证
        if format_result.url_type in [
            URLType.LINKEDIN_COMPANY,
            URLType.LINKEDIN_PERSON,
            URLType.LINKEDIN_JOB
        ] or 'linkedin.com' in url.lower():
            linkedin_result = validate_linkedin_url(url)
            if linkedin_result.status == URLValidationStatus.INVALID:
                return linkedin_result

        # 可达性验证
        if self.check_accessibility:
            return await check_url_accessibility(
                url, field_name, timeout=self.timeout
            )

        return format_result

    async def validate_all(
        self,
        project: dict,
        url_fields: List[str] = None
    ) -> Dict[str, URLValidationResult]:
        """
        验证项目中的所有 URL

        Args:
            project: 项目字典
            url_fields: 要验证的 URL 字段列表

        Returns:
            字段名到验证结果的映射
        """
        if url_fields is None:
            url_fields = ['website', 'linkedin', 'platform_link']

        results = {}
        tasks = []

        for field_name in url_fields:
            url = project.get(field_name)
            if url:
                tasks.append(self.validate(url, field_name))
            else:
                results[field_name] = URLValidationResult(
                    url="",
                    field_name=field_name,
                    status=URLValidationStatus.INVALID,
                    message=f"{field_name} 为空"
                )

        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    field_name = url_fields[i]
                    results[field_name] = URLValidationResult(
                        url=project.get(field_name, ""),
                        field_name=field_name,
                        status=URLValidationStatus.UNKNOWN,
                        message=f"验证出错: {str(result)[:50]}"
                    )
                else:
                    results[result.field_name] = result

        return results

    async def validate_batch(
        self,
        urls: List[Tuple[str, str]],
        max_concurrent: int = 10
    ) -> List[URLValidationResult]:
        """
        批量验证 URL

        Args:
            urls: (url, field_name) 元组列表
            max_concurrent: 最大并发数

        Returns:
            验证结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_with_semaphore(
            url: str, field_name: str
        ) -> URLValidationResult:
            async with semaphore:
                return await self.validate(url, field_name)

        tasks = [
            validate_with_semaphore(url, field_name)
            for url, field_name in urls
        ]
        return await asyncio.gather(*tasks)


# ============================================
# Convenience Functions
# ============================================

def quick_validate_url(url: str, field_name: str = "url") -> URLValidationResult:
    """快速验证 URL 格式（同步）"""
    return validate_url_format(url, field_name)


async def full_validate_url(
    url: str,
    field_name: str = "url",
    timeout: int = 5
) -> URLValidationResult:
    """完整验证 URL（异步）"""
    validator = SmartURLValidator(
        check_accessibility=True,
        timeout=timeout
    )
    return await validator.validate(url, field_name)


# ============================================
# Sync Wrapper
# ============================================

def validate_url_sync(
    url: str,
    field_name: str = "url",
    check_accessibility: bool = False,
    timeout: int = 5
) -> URLValidationResult:
    """
    同步验证 URL

    用于不需要异步的场景
    """
    # 格式验证
    format_result = validate_url_format(url, field_name)
    if format_result.status == URLValidationStatus.INVALID:
        return format_result

    # 如果需要可达性验证
    if check_accessibility:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            check_url_accessibility(url, field_name, timeout)
        )

    return format_result


# ============================================
# CLI Entry Point
# ============================================

def main():
    """命令行测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Smart URL Validator')
    parser.add_argument('url', help='URL to validate')
    parser.add_argument('--check-access', action='store_true',
                       help='Check URL accessibility')
    parser.add_argument('--timeout', type=int, default=5,
                       help='Request timeout in seconds')

    args = parser.parse_args()

    result = validate_url_sync(
        args.url,
        check_accessibility=args.check_access,
        timeout=args.timeout
    )

    print(f"\nURL: {result.url}")
    print(f"Status: {result.status.value}")
    print(f"Type: {result.url_type.value}")
    print(f"Message: {result.message}")
    if result.http_code:
        print(f"HTTP Code: {result.http_code}")
    if result.final_url and result.final_url != result.url:
        print(f"Final URL: {result.final_url}")
    if result.details:
        print(f"Details: {result.details}")


if __name__ == "__main__":
    main()
