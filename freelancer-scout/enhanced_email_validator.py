#!/usr/bin/env python3
"""
Enhanced Email Validator Module
多层邮箱验证：格式 → MX记录 → 一次性邮箱检测 → SMTP验证

Features:
- Multi-tier validation for higher accuracy
- Disposable email detection
- MX record caching
- SMTP retry with exponential backoff
- Async support for parallel validation
"""

import re
import asyncio
import socket
import smtplib
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """验证状态"""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    RISKY = "risky"  # 可疑但不确定无效


class EmailType(Enum):
    """邮箱类型"""
    CORPORATE = "corporate"
    FREE = "free"
    DISPOSABLE = "disposable"
    UNKNOWN = "unknown"


@dataclass
class EmailValidationResult:
    """邮箱验证结果"""
    email: str
    status: ValidationStatus
    message: str
    email_type: EmailType = EmailType.UNKNOWN
    tier_reached: int = 0  # 验证到第几层
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'email': self.email,
            'status': self.status.value,
            'message': self.message,
            'email_type': self.email_type.value,
            'tier_reached': self.tier_reached,
            'details': self.details
        }

    @property
    def is_valid(self) -> bool:
        return self.status == ValidationStatus.VALID

    @property
    def is_invalid(self) -> bool:
        return self.status == ValidationStatus.INVALID


# ============================================
# Constants and Patterns
# ============================================

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Common free email providers
FREE_EMAIL_DOMAINS = {
    # International
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com',
    'aol.com', 'icloud.com', 'protonmail.com', 'proton.me', 'zoho.com',
    'yandex.com', 'mail.com', 'gmx.com', 'gmx.net',
    # China
    'qq.com', '163.com', '126.com', 'foxmail.com', 'sina.com', 'sohu.com',
    'yeah.net', 'aliyun.com', '139.com', '189.cn',
    # Other regions
    'mail.ru', 'rambler.ru', 'ukr.net', 'rediffmail.com'
}


# ============================================
# MX Record Cache
# ============================================

class MXCache:
    """MX 记录缓存"""
    def __init__(self, ttl_hours: int = 24):
        self._cache: Dict[str, Tuple[List[str], datetime]] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, domain: str) -> Optional[List[str]]:
        """获取缓存的 MX 记录"""
        if domain in self._cache:
            mx_records, cached_at = self._cache[domain]
            if datetime.now() - cached_at < self._ttl:
                return mx_records
            else:
                del self._cache[domain]
        return None

    def set(self, domain: str, mx_records: List[str]):
        """设置 MX 记录缓存"""
        self._cache[domain] = (mx_records, datetime.now())

    def clear(self):
        """清除缓存"""
        self._cache.clear()


# Global MX cache
_mx_cache = MXCache()


# ============================================
# Tier 1: Syntax Validation
# ============================================

def validate_email_syntax(email: str) -> EmailValidationResult:
    """
    Tier 1: 邮箱格式验证

    检查：
    - 是否为空
    - 是否是字符串
    - 是否符合邮箱正则表达式
    """
    if not email or not isinstance(email, str):
        return EmailValidationResult(
            email=str(email) if email else "",
            status=ValidationStatus.INVALID,
            message="邮箱为空或格式错误",
            tier_reached=1
        )

    email = email.strip().lower()

    if not EMAIL_PATTERN.match(email):
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message=f"邮箱格式不正确: {email}",
            tier_reached=1
        )

    # 检查邮箱类型
    domain = email.split('@')[-1]
    if domain in FREE_EMAIL_DOMAINS:
        email_type = EmailType.FREE
    else:
        email_type = EmailType.CORPORATE

    return EmailValidationResult(
        email=email,
        status=ValidationStatus.VALID,
        message="邮箱格式正确",
        email_type=email_type,
        tier_reached=1,
        details={'domain': domain}
    )


# ============================================
# Tier 2: MX Record Validation
# ============================================

def validate_mx_record(email: str, timeout: int = 5) -> EmailValidationResult:
    """
    Tier 2: MX 记录验证

    检查域名是否有有效的邮件服务器配置
    """
    if '@' not in email:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message="邮箱格式无效",
            tier_reached=2
        )

    domain = email.split('@')[-1].lower()

    # 检查缓存
    cached_mx = _mx_cache.get(domain)
    if cached_mx is not None:
        if cached_mx:
            return EmailValidationResult(
                email=email,
                status=ValidationStatus.VALID,
                message=f"域名 {domain} 有有效的 MX 记录（缓存）",
                tier_reached=2,
                details={'mx_records': cached_mx, 'cached': True}
            )
        else:
            return EmailValidationResult(
                email=email,
                status=ValidationStatus.INVALID,
                message=f"域名 {domain} 无 MX 记录（缓存）",
                tier_reached=2
            )

    # 查询 MX 记录
    try:
        import dns.resolver

        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        mx_records = resolver.resolve(domain, 'MX')
        mx_hosts = [str(r.exchange).rstrip('.') for r in mx_records]

        if mx_hosts:
            _mx_cache.set(domain, mx_hosts)
            return EmailValidationResult(
                email=email,
                status=ValidationStatus.VALID,
                message=f"域名 {domain} 有 {len(mx_hosts)} 个 MX 记录",
                tier_reached=2,
                details={'mx_records': mx_hosts[:3]}  # 只保留前3个
            )
        else:
            _mx_cache.set(domain, [])
            return EmailValidationResult(
                email=email,
                status=ValidationStatus.INVALID,
                message=f"域名 {domain} 无 MX 记录",
                tier_reached=2
            )

    except ImportError:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.UNKNOWN,
            message="DNS 模块未安装，跳过 MX 验证",
            tier_reached=2,
            details={'error': 'dnspython not installed'}
        )
    except dns.resolver.NXDOMAIN:
        _mx_cache.set(domain, [])
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message=f"域名 {domain} 不存在",
            tier_reached=2
        )
    except dns.resolver.NoAnswer:
        _mx_cache.set(domain, [])
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message=f"域名 {domain} 无 MX 记录",
            tier_reached=2
        )
    except dns.resolver.Timeout:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.UNKNOWN,
            message="DNS 查询超时",
            tier_reached=2
        )
    except Exception as e:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.UNKNOWN,
            message=f"MX 验证失败: {str(e)[:50]}",
            tier_reached=2
        )


# ============================================
# Tier 3: Disposable Email Detection
# ============================================

def load_disposable_domains() -> set:
    """加载一次性邮箱域名列表"""
    domains = set()

    # 尝试从文件加载
    domain_file = Path(__file__).parent / "disposable_domains.txt"
    if domain_file.exists():
        with open(domain_file, 'r') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    domains.add(line)

    # 添加常见的一次性邮箱域名
    common_disposable = {
        # 常见一次性邮箱服务
        'tempmail.com', 'temp-mail.org', 'guerrillamail.com', 'guerrillamail.org',
        'mailinator.com', '10minutemail.com', 'throwaway.email', 'fakeinbox.com',
        'maildrop.cc', 'sharklasers.com', 'trashmail.com', 'getnada.com',
        'mohmal.com', 'tempail.com', 'emailondeck.com', 'dispostable.com',
        'mailnesia.com', 'mintemail.com', 'mt2015.com', 'nwytg.net',
        'spamgourmet.com', 'yopmail.com', 'yopmail.fr', 'yopmail.net',
        # 更多一次性邮箱
        'mailcatch.com', 'tempmailaddress.com', 'burnermail.io',
        'tempmailo.com', 'discard.email', 'mailsac.com', 'inboxalias.com',
        'jetable.org', 'mytrashmail.com', 'fakemailgenerator.com',
        'temporary-mail.net', 'emailfake.com', 'crazymailing.com',
        'tempr.email', 'fakemail.net', 'dropmail.me', 'harakirimail.com',
    }
    domains.update(common_disposable)

    return domains


# Lazy-loaded disposable domains
_disposable_domains: Optional[set] = None


def get_disposable_domains() -> set:
    """获取一次性邮箱域名集合（延迟加载）"""
    global _disposable_domains
    if _disposable_domains is None:
        _disposable_domains = load_disposable_domains()
    return _disposable_domains


def validate_not_disposable(email: str) -> EmailValidationResult:
    """
    Tier 3: 一次性邮箱检测

    检查邮箱是否来自一次性邮箱服务
    """
    if '@' not in email:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message="邮箱格式无效",
            tier_reached=3
        )

    domain = email.split('@')[-1].lower()
    disposable_domains = get_disposable_domains()

    if domain in disposable_domains:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message=f"一次性邮箱: {domain}",
            email_type=EmailType.DISPOSABLE,
            tier_reached=3,
            details={'is_disposable': True, 'domain': domain}
        )

    # 检查常见模式
    disposable_patterns = [
        r'temp.*mail', r'throw.*away', r'fake.*mail', r'trash.*mail',
        r'spam.*', r'junk.*mail', r'burner.*', r'10.*minute'
    ]

    for pattern in disposable_patterns:
        if re.search(pattern, domain, re.IGNORECASE):
            return EmailValidationResult(
                email=email,
                status=ValidationStatus.RISKY,
                message=f"疑似一次性邮箱: {domain}",
                email_type=EmailType.DISPOSABLE,
                tier_reached=3,
                details={'suspicious_pattern': pattern}
            )

    return EmailValidationResult(
        email=email,
        status=ValidationStatus.VALID,
        message="非一次性邮箱",
        tier_reached=3
    )


# ============================================
# Tier 4: SMTP Validation with Retry
# ============================================

def validate_smtp_with_retry(
    email: str,
    timeout: int = 10,
    max_retries: int = 2,
    sender_email: str = "verify@example.com"
) -> EmailValidationResult:
    """
    Tier 4: SMTP 验证（带重试）

    通过 SMTP 握手验证邮箱是否存在
    包含指数退避重试机制
    """
    if '@' not in email:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message="邮箱格式无效",
            tier_reached=4
        )

    domain = email.split('@')[-1].lower()

    # 获取 MX 记录
    cached_mx = _mx_cache.get(domain)
    if cached_mx:
        mx_hosts = cached_mx
    else:
        try:
            import dns.resolver
            resolver = dns.resolver.Resolver()
            resolver.timeout = timeout
            mx_records = resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange).rstrip('.') for r in mx_records]
            _mx_cache.set(domain, mx_hosts)
        except Exception:
            return EmailValidationResult(
                email=email,
                status=ValidationStatus.UNKNOWN,
                message="无法获取 MX 记录",
                tier_reached=4
            )

    if not mx_hosts:
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.INVALID,
            message="域名无 MX 记录",
            tier_reached=4
        )

    # 尝试多个 MX 服务器
    last_error = None
    for mx_host in mx_hosts[:3]:  # 最多尝试3个 MX
        for attempt in range(max_retries + 1):
            try:
                # 指数退避
                if attempt > 0:
                    import time
                    time.sleep(2 ** attempt)

                server = smtplib.SMTP(mx_host, timeout=timeout)
                server.ehlo()

                # 发送验证命令
                server.mail(sender_email)
                code, message = server.rcpt(email)
                server.quit()

                # 解析响应码
                if code == 250:
                    return EmailValidationResult(
                        email=email,
                        status=ValidationStatus.VALID,
                        message="邮箱存在（SMTP 验证通过）",
                        tier_reached=4,
                        details={'smtp_code': code, 'mx_host': mx_host}
                    )
                elif code in [550, 551, 552, 553]:
                    return EmailValidationResult(
                        email=email,
                        status=ValidationStatus.INVALID,
                        message="邮箱不存在",
                        tier_reached=4,
                        details={'smtp_code': code, 'mx_host': mx_host}
                    )
                elif code in [450, 451, 452]:
                    # 临时错误，继续重试
                    last_error = f"临时错误 (code={code})"
                    continue
                else:
                    return EmailValidationResult(
                        email=email,
                        status=ValidationStatus.UNKNOWN,
                        message=f"SMTP 验证不确定 (code={code})",
                        tier_reached=4,
                        details={'smtp_code': code}
                    )

            except smtplib.SMTPRecipientsRefused:
                return EmailValidationResult(
                    email=email,
                    status=ValidationStatus.INVALID,
                    message="邮箱被服务器拒绝",
                    tier_reached=4
                )
            except smtplib.SMTPConnectError:
                last_error = f"无法连接 {mx_host}"
                continue
            except smtplib.SMTPSenderRefused:
                # 一些服务器拒绝验证，无法确定
                return EmailValidationResult(
                    email=email,
                    status=ValidationStatus.UNKNOWN,
                    message="邮件服务器拒绝验证",
                    tier_reached=4,
                    details={'mx_host': mx_host}
                )
            except (socket.timeout, TimeoutError):
                last_error = f"连接 {mx_host} 超时"
                continue
            except Exception as e:
                last_error = str(e)[:50]
                continue

    return EmailValidationResult(
        email=email,
        status=ValidationStatus.UNKNOWN,
        message=f"SMTP 验证失败: {last_error}",
        tier_reached=4,
        details={'last_error': last_error}
    )


# ============================================
# Main Validator Class
# ============================================

class EnhancedEmailValidator:
    """
    增强型邮箱验证器

    多层验证策略：
    - Tier 1: 格式验证（即时）
    - Tier 2: MX 记录验证（快速）
    - Tier 3: 一次性邮箱检测（即时）
    - Tier 4: SMTP 验证（较慢，可选）
    """

    def __init__(
        self,
        check_mx: bool = True,
        check_disposable: bool = True,
        check_smtp: bool = False,  # 默认关闭，较慢且可能被拦截
        smtp_timeout: int = 10,
        smtp_retries: int = 2
    ):
        self.check_mx = check_mx
        self.check_disposable = check_disposable
        self.check_smtp = check_smtp
        self.smtp_timeout = smtp_timeout
        self.smtp_retries = smtp_retries

    def validate(self, email: str) -> EmailValidationResult:
        """
        同步验证邮箱

        按层级验证，任一层确定无效则立即返回
        """
        if not email:
            return EmailValidationResult(
                email="",
                status=ValidationStatus.INVALID,
                message="邮箱为空",
                tier_reached=0
            )

        email = email.strip().lower()

        # Tier 1: 格式验证
        result = validate_email_syntax(email)
        if result.status == ValidationStatus.INVALID:
            return result

        email_type = result.email_type
        domain = result.details.get('domain', '')

        # Tier 2: MX 记录验证
        if self.check_mx:
            result = validate_mx_record(email)
            if result.status == ValidationStatus.INVALID:
                result.email_type = email_type
                return result

        # Tier 3: 一次性邮箱检测
        if self.check_disposable:
            result = validate_not_disposable(email)
            if result.status == ValidationStatus.INVALID:
                return result
            if result.email_type == EmailType.DISPOSABLE:
                email_type = EmailType.DISPOSABLE

        # Tier 4: SMTP 验证
        if self.check_smtp:
            result = validate_smtp_with_retry(
                email,
                timeout=self.smtp_timeout,
                max_retries=self.smtp_retries
            )
            result.email_type = email_type
            return result

        # 返回最终结果
        return EmailValidationResult(
            email=email,
            status=ValidationStatus.VALID,
            message="邮箱验证通过",
            email_type=email_type,
            tier_reached=3 if self.check_disposable else 2,
            details={'domain': domain}
        )

    async def validate_async(self, email: str) -> EmailValidationResult:
        """
        异步验证邮箱（用于批量并行验证）
        """
        # 使用线程池执行同步验证
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.validate, email)

    async def validate_batch(
        self,
        emails: List[str],
        max_concurrent: int = 10
    ) -> List[EmailValidationResult]:
        """
        批量异步验证邮箱

        Args:
            emails: 邮箱列表
            max_concurrent: 最大并发数

        Returns:
            验证结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_with_semaphore(email: str) -> EmailValidationResult:
            async with semaphore:
                return await self.validate_async(email)

        tasks = [validate_with_semaphore(email) for email in emails]
        return await asyncio.gather(*tasks)


# ============================================
# Convenience Functions
# ============================================

def quick_validate(email: str) -> EmailValidationResult:
    """快速验证（仅格式和一次性检测）"""
    validator = EnhancedEmailValidator(
        check_mx=False,
        check_disposable=True,
        check_smtp=False
    )
    return validator.validate(email)


def full_validate(email: str) -> EmailValidationResult:
    """完整验证（包含 SMTP）"""
    validator = EnhancedEmailValidator(
        check_mx=True,
        check_disposable=True,
        check_smtp=True
    )
    return validator.validate(email)


# ============================================
# CLI Entry Point
# ============================================

def main():
    """命令行测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Email Validator')
    parser.add_argument('email', help='Email address to validate')
    parser.add_argument('--full', action='store_true', help='Full validation with SMTP')
    parser.add_argument('--no-mx', action='store_true', help='Skip MX record check')

    args = parser.parse_args()

    validator = EnhancedEmailValidator(
        check_mx=not args.no_mx,
        check_disposable=True,
        check_smtp=args.full
    )

    result = validator.validate(args.email)

    print(f"\nEmail: {result.email}")
    print(f"Status: {result.status.value}")
    print(f"Type: {result.email_type.value}")
    print(f"Message: {result.message}")
    print(f"Tier Reached: {result.tier_reached}")
    if result.details:
        print(f"Details: {result.details}")


if __name__ == "__main__":
    main()
