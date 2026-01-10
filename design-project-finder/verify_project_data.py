#!/usr/bin/env python3
"""
Project Data Verification Module
校验设计项目数据的有效性：邮箱、链接、活跃度

使用方式:
    # 快速校验（仅格式）
    python3 design-project-finder/verify_project_data.py

    # 完整校验（含链接可访问性和活跃度）
    python3 design-project-finder/verify_project_data.py --full-check
"""

import re
import asyncio
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ValidationStatus(Enum):
    """校验状态枚举"""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    PENDING = "pending"


@dataclass
class ValidationResult:
    """校验结果数据类"""
    field: str
    status: ValidationStatus
    message: str
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            'field': self.field,
            'status': self.status.value,
            'message': self.message,
            'details': self.details
        }


# ============================================
# 邮箱格式验证
# ============================================

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

FREE_EMAIL_DOMAINS = [
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'qq.com', '163.com', 'foxmail.com', 'live.com'
]


def validate_email(email: Any) -> ValidationResult:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        ValidationResult: 校验结果
    """
    if email is None or (isinstance(email, str) and not email.strip()):
        return ValidationResult(
            field="email",
            status=ValidationStatus.INVALID,
            message="邮箱为空"
        )

    if not isinstance(email, str):
        return ValidationResult(
            field="email",
            status=ValidationStatus.INVALID,
            message="邮箱格式错误：不是字符串类型"
        )

    email = email.strip().lower()

    # 检查常见免费邮箱（非企业邮箱降低优先级）
    domain = email.split('@')[-1] if '@' in email else ''
    is_free_email = any(domain.endswith(d) for d in FREE_EMAIL_DOMAINS)

    if EMAIL_PATTERN.match(email):
        if is_free_email:
            return ValidationResult(
                field="email",
                status=ValidationStatus.VALID,
                message="邮箱格式正确（免费邮箱）",
                details={"email": email, "is_free_email": True}
            )
        return ValidationResult(
            field="email",
            status=ValidationStatus.VALID,
            message="邮箱格式正确（企业邮箱）",
            details={"email": email, "is_free_email": False}
        )

    return ValidationResult(
        field="email",
        status=ValidationStatus.INVALID,
        message=f"邮箱格式错误: {email}"
    )


# ============================================
# SMTP 邮箱存在性验证
# ============================================

def verify_email_exists_smtp(email: str, timeout: int = 10) -> ValidationResult:
    """
    通过 SMTP 握手验证邮箱是否真实存在

    Args:
        email: 邮箱地址
        timeout: 连接超时时间（秒）

    Returns:
        ValidationResult: 校验结果
    """
    if not email or '@' not in email:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.INVALID,
            message="邮箱格式无效"
        )

    domain = email.split('@')[-1].lower()

    # 检查是否安装了 dns 模块
    try:
        import dns.resolver
    except ImportError:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message="DNS 模块未安装，跳过邮箱验证",
            details={"email": email, "error": "dnspython not installed"}
        )

    # 查询 MX 记录
    try:
        mx_records = dns.resolver.resolve(domain, 'MX', lifetime=timeout)
        if not mx_records:
            return ValidationResult(
                field="email_exists",
                status=ValidationStatus.INVALID,
                message=f"域名 {domain} 无 MX 记录",
                details={"domain": domain}
            )
    except dns.resolver.NoAnswer:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.INVALID,
            message=f"域名 {domain} 无 MX 记录",
            details={"domain": domain, "error": "No MX records found"}
        )
    except dns.resolver.NXDOMAIN:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.INVALID,
            message=f"域名 {domain} 不存在",
            details={"domain": domain, "error": "NXDOMAIN"}
        )
    except dns.resolver.Timeout:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message=f"DNS 查询超时",
            details={"domain": domain, "error": "DNS timeout"}
        )
    except Exception as e:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message=f"DNS 查询失败: {str(e)[:50]}",
            details={"domain": domain, "error": str(e)[:100]}
        )

    # SMTP 握手验证
    try:
        import smtplib
        mx_host = str(mx_records[0].exchange).rstrip('.')
        server = smtplib.SMTP(mx_host, timeout=timeout)
        server.ehlo()

        # 尝试 RCPT TO 命令验证邮箱
        server.mail('verify@example.com')
        code, message = server.rcpt(email)
        server.quit()

        # 250 = 邮箱存在, 550/551/552 = 邮箱不存在, 450/451 = 临时错误
        if code == 250:
            return ValidationResult(
                field="email_exists",
                status=ValidationStatus.VALID,
                message="邮箱存在（SMTP 验证通过）",
                details={"email": email, "smtp_code": code}
            )
        elif code in [550, 551, 552]:
            return ValidationResult(
                field="email_exists",
                status=ValidationStatus.INVALID,
                message="邮箱不存在",
                details={"email": email, "smtp_code": code, "smtp_message": message.decode()}
            )
        else:
            return ValidationResult(
                field="email_exists",
                status=ValidationStatus.UNKNOWN,
                message=f"SMTP 验证结果不确定 (code={code})",
                details={"email": email, "smtp_code": code, "smtp_message": message.decode()}
            )

    except smtplib.SMTPConnectError:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message=f"无法连接邮件服务器",
            details={"email": email, "mx_host": mx_host, "error": "Connection error"}
        )
    except smtplib.SMTPSenderRefused:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message=f"邮件服务器拒绝连接",
            details={"email": email, "error": "Sender refused"}
        )
    except smtplib.SMTPRecipientsRefused:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.INVALID,
            message="邮箱被服务器拒绝",
            details={"email": email, "error": "Recipients refused"}
        )
    except smtplib.SMTPException as e:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message=f"SMTP 错误: {str(e)[:50]}",
            details={"email": email, "error": str(e)[:100]}
        )
    except TimeoutError:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message="SMTP 连接超时",
            details={"email": email, "error": "Timeout"}
        )
    except Exception as e:
        return ValidationResult(
            field="email_exists",
            status=ValidationStatus.UNKNOWN,
            message=f"验证出错: {str(e)[:50]}",
            details={"email": email, "error": str(e)[:100]}
        )


# ============================================
# 链接格式验证
# ============================================

def validate_url(url: Any, field_name: str) -> ValidationResult:
    """
    验证 URL 格式

    Args:
        url: URL 字符串
        field_name: 字段名称 (website, linkedin, platform_link)

    Returns:
        ValidationResult: 校验结果
    """
    if url is None or (isinstance(url, str) and not url.strip()):
        return ValidationResult(
            field=field_name,
            status=ValidationStatus.INVALID,
            message=f"{field_name} 为空"
        )

    if not isinstance(url, str):
        return ValidationResult(
            field=field_name,
            status=ValidationStatus.INVALID,
            message=f"{field_name} 格式错误：不是字符串类型"
        )

    url = url.strip()

    # 检查是否包含 http/https 前缀
    if not url.lower().startswith(('http://', 'https://')):
        return ValidationResult(
            field=field_name,
            status=ValidationStatus.INVALID,
            message=f"{field_name} 缺少协议前缀: {url}"
        )

    # 基础 URL 格式验证
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        if result.netloc:
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.VALID,
                message=f"{field_name} 格式正确",
                details={"url": url}
            )
        else:
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.INVALID,
                message=f"{field_name} 格式错误: 无效的域名"
            )
    except Exception:
        return ValidationResult(
            field=field_name,
            status=ValidationStatus.INVALID,
            message=f"{field_name} 格式错误: {url}"
        )


# ============================================
# 链接可访问性验证 (使用 Playwright MCP)
# ============================================

async def check_link_accessibility_mcp(url: str, field_name: str) -> ValidationResult:
    """
    使用 Playwright MCP 检查链接是否可访问

    Args:
        url: 要检查的 URL
        field_name: 字段名称

    Returns:
        ValidationResult: 校验结果
    """
    if not url or not url.startswith('http'):
        return ValidationResult(
            field=field_name,
            status=ValidationStatus.INVALID,
            message=f"{field_name} 无效或为空"
        )

    try:
        # 使用 Playwright MCP 导航并检查
        from mcp_playwright import browser_navigate, browser_evaluate

        # 导航到 URL
        await browser_navigate(url=url)

        # 检查页面是否成功加载（获取页面标题或内容）
        page_info = await browser_evaluate(
            function="() => ({ title: document.title, bodyLength: document.body.innerText.length })",
            element=f"{field_name} page"
        )

        if page_info and page_info.get('title') is not None:
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.VALID,
                message=f"{field_name} 可正常访问",
                details={"url": url, "title": page_info.get('title', '')[:100]}
            )
        else:
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.INVALID,
                message=f"{field_name} 页面无法加载或为空"
            )

    except Exception as e:
        error_msg = str(e)
        # 处理常见的网络错误
        if '404' in error_msg or 'Not Found' in error_msg:
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.INVALID,
                message=f"{field_name} 页面不存在 (404)"
            )
        elif 'timeout' in error_msg.lower():
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.UNKNOWN,
                message=f"{field_name} 访问超时"
            )
        else:
            return ValidationResult(
                field=field_name,
                status=ValidationStatus.UNKNOWN,
                message=f"{field_name} 访问出错: {error_msg[:100]}"
            )


# ============================================
# 项目活跃度验证 (使用 Exa AI)
# ============================================

def create_activity_query(project: dict) -> str:
    """
    为项目创建活跃度搜索查询

    Args:
        project: 项目数据字典

    Returns:
        str: 搜索查询字符串
    """
    client = project.get('client', '')
    title = project.get('title', '')
    platform = project.get('platform', '')

    # 构建搜索查询
    query_parts = [f'"{client}"']
    if title:
        # 提取关键职位名称
        keywords = ['designer', 'developer', 'UI', 'UX', 'product']
        for kw in keywords:
            if kw.lower() in title.lower():
                query_parts.append(kw)
                break

    if platform:
        query_parts.append(f"site:{platform.lower().replace(' ', '')}.com")

    return ' '.join(query_parts) + ' hiring designer OR "looking for" OR "project"'


async def check_project_activity_mcp(project: dict) -> ValidationResult:
    """
    使用 Exa AI 检查项目是否仍然活跃

    Args:
        project: 项目数据字典

    Returns:
        ValidationResult: 校验结果
    """
    client = project.get('client', 'Unknown')
    query = create_activity_query(project)

    try:
        # 使用 Exa MCP web search
        from mcp_exa import web_search_exa

        results = await web_search_exa(
            query=query,
            numResults=5
        )

        if not results or len(results) == 0:
            return ValidationResult(
                field="activity",
                status=ValidationStatus.UNKNOWN,
                message=f"无法确认 {client} 的项目活跃度（无搜索结果）"
            )

        # 分析搜索结果，检查是否有项目仍然开放的信息
        activity_keywords = ['hiring', 'looking for', 'designer needed', 'open role',
                            'project available', 'freelance', 'contract']

        relevant_count = 0
        for r in results:
            content = r.get('content', '').lower() if isinstance(r, dict) else str(r).lower()
            if any(kw in content for kw in activity_keywords):
                relevant_count += 1

        if relevant_count > 0:
            return ValidationResult(
                field="activity",
                status=ValidationStatus.VALID,
                message=f"{client} 项目仍在活跃招聘",
                details={"matched_results": relevant_count, "total_results": len(results)}
            )
        else:
            return ValidationResult(
                field="activity",
                status=ValidationStatus.INVALID,
                message=f"{client} 可能已停止招聘（搜索结果无相关职位）",
                details={"total_results": len(results)}
            )

    except Exception as e:
        return ValidationResult(
            field="activity",
            status=ValidationStatus.UNKNOWN,
            message=f"活跃度检查失败: {str(e)[:100]}"
        )


# ============================================
# 格式验证（不依赖外部工具）
# ============================================

def validate_link_accessibility_fake(url: str, field_name: str) -> ValidationResult:
    """
    模拟链接可访问性验证（不依赖 Playwright）
    用于快速校验模式

    Args:
        url: URL 字符串
        field_name: 字段名称

    Returns:
        ValidationResult: 校验结果
    """
    if not url or not url.startswith('http'):
        return ValidationResult(
            field=field_name,
            status=ValidationStatus.INVALID,
            message=f"{field_name} 无效或为空"
        )

    # 只做格式验证，不检查实际可访问性
    return ValidationResult(
        field=field_name,
        status=ValidationStatus.VALID,
        message=f"{field_name} 格式正确（未检查可访问性）",
        details={"url": url, "checked": False}
    )


def check_project_activity_fake(project: dict) -> ValidationResult:
    """
    模拟项目活跃度验证（不依赖 Exa）
    用于快速校验模式

    Args:
        project: 项目数据字典

    Returns:
        ValidationResult: 校验结果
    """
    client = project.get('client', 'Unknown')
    return ValidationResult(
        field="activity",
        status=ValidationStatus.UNKNOWN,
        message=f"{client} 活跃度未检查（需要 Exa API）",
        details={"checked": False}
    )


# ============================================
# 综合校验函数
# ============================================

async def verify_project(
    project: dict,
    check_accessibility: bool = False,
    check_activity: bool = False
) -> dict:
    """
    综合校验单个项目

    Args:
        project: 项目数据字典
        check_accessibility: 是否检查链接可访问性（需要 Playwright MCP）
        check_activity: 是否检查项目活跃度（需要 Exa AI MCP）

    Returns:
        dict: 带校验结果的项目数据
    """
    result = project.copy()
    validation_results: List[ValidationResult] = []
    is_valid_overall = True

    # 1. 邮箱格式验证
    email_result = validate_email(project.get('email'))
    validation_results.append(email_result)
    if email_result.status == ValidationStatus.INVALID:
        is_valid_overall = False

    # 2. 链接格式验证
    for link_field in ['website', 'linkedin', 'platform_link']:
        url = project.get(link_field)
        if url:
            url_result = validate_url(url, link_field)
            validation_results.append(url_result)
            if url_result.status == ValidationStatus.INVALID:
                is_valid_overall = False

    # 3. 链接可访问性验证（可选）
    if check_accessibility:
        for link_field in ['website', 'linkedin']:
            url = project.get(link_field)
            if url:
                accessibility_result = await check_link_accessibility_mcp(url, link_field)
                validation_results.append(accessibility_result)
                if accessibility_result.status == ValidationStatus.INVALID:
                    is_valid_overall = False

    # 4. 活跃度验证（可选）
    if check_activity:
        activity_result = await check_project_activity_mcp(project)
        validation_results.append(activity_result)
        if activity_result.status == ValidationStatus.INVALID:
            is_valid_overall = False

    # 添加校验结果到项目
    result['is_valid'] = is_valid_overall
    result['validation_notes'] = [
        r.message for r in validation_results if r.status != ValidationStatus.VALID
    ]
    result['validation_results'] = [r.to_dict() for r in validation_results]
    result['validated_at'] = datetime.now().isoformat()

    return result


def verify_project_sync(
    project: dict,
    check_accessibility: bool = False,
    check_activity: bool = False
) -> dict:
    """
    同步版本校验（不依赖异步 MCP）
    """
    result = project.copy()
    validation_results: List[Dict] = []
    is_valid_overall = True

    # 1. 邮箱格式验证
    email_result = validate_email(project.get('email'))
    validation_results.append(email_result.to_dict())
    if email_result.status == ValidationStatus.INVALID:
        is_valid_overall = False

    # 2. 链接格式验证
    for link_field in ['website', 'linkedin', 'platform_link']:
        url = project.get(link_field)
        if url:
            url_result = validate_url(url, link_field)
            validation_results.append(url_result.to_dict())
            if url_result.status == ValidationStatus.INVALID:
                is_valid_overall = False

    # 3. 链接可访问性验证（可选，模拟）
    if check_accessibility:
        for link_field in ['website', 'linkedin']:
            url = project.get(link_field)
            if url:
                accessibility_result = validate_link_accessibility_fake(url, link_field)
                validation_results.append(accessibility_result.to_dict())

    # 4. 活跃度验证（可选，模拟）
    if check_activity:
        activity_result = check_project_activity_fake(project)
        validation_results.append(activity_result.to_dict())

    # 添加校验结果
    result['is_valid'] = is_valid_overall
    result['validation_notes'] = [
        r['message'] for r in validation_results if r['status'] != 'valid'
    ]
    result['validation_results'] = validation_results
    result['validated_at'] = datetime.now().isoformat()

    return result


# ============================================
# 批量处理函数
# ============================================

def filter_valid_projects(projects: list, remove_invalid: bool = True) -> tuple:
    """
    过滤项目列表

    Args:
        projects: 项目列表
        remove_invalid: 是否移除无效项目

    Returns:
        tuple: (有效项目列表, 无效项目列表)
    """
    valid_projects = []
    invalid_projects = []

    for project in projects:
        is_valid = project.get('is_valid', True)
        if is_valid:
            valid_projects.append(project)
        else:
            invalid_projects.append(project)

    if remove_invalid:
        return valid_projects, invalid_projects
    else:
        # 返回全部，但在输出中标记
        return projects, invalid_projects


def load_research_data() -> list:
    """从 process_design_projects.py 加载研究数据"""
    import importlib.util

    # Navigate to project root (parent of design-project-finder)
    project_root = Path(__file__).parent.parent
    script_path = project_root / "process_design_projects.py"

    # 读取文件内容
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 research_data
    import re
    match = re.search(r'research_data\s*=\s*(\{.*?\})\n', content, re.DOTALL)
    if not match:
        # 尝试更宽松的匹配
        match = re.search(r'research_data\s*=\s*(\{[^}]+(?:\{[^}]+\}[^}]*)*\})', content, re.DOTALL)

    if match:
        import ast
        research_data = ast.literal_eval(match.group(1))
        all_projects = []
        for platform, projects in research_data.items():
            for p in projects:
                p['platform'] = platform
                all_projects.append(p)
        return all_projects

    return []


# ============================================
# 独立校验脚本入口
# ============================================

async def run_verification_async(
    data_source: str = None,
    output_file: str = None,
    check_accessibility: bool = False,
    check_activity: bool = False
):
    """异步运行校验任务"""
    print("=" * 60)
    print("Project Data Verification")
    print("=" * 60)

    # 加载数据
    if data_source and Path(data_source).exists():
        with open(data_source, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_projects = data.get('projects', data)
        print(f"\nLoaded {len(all_projects)} projects from {data_source}")
    else:
        all_projects = load_research_data()
        print(f"\nLoaded {len(all_projects)} projects from process_design_projects.py")

    if not all_projects:
        print("ERROR: No projects found to verify")
        return []

    # 运行校验
    print(f"\n[1/2] Verifying {len(all_projects)} projects...")
    if check_accessibility:
        print("   - Checking link accessibility (may take time)")
    if check_activity:
        print("   - Checking project activity (requires Exa API)")

    verified_projects = []
    for i, project in enumerate(all_projects, 1):
        client = project.get('client', 'Unknown')
        print(f"   [{i}/{len(all_projects)}] {client}", end='\r')

        verified = await verify_project(
            project,
            check_accessibility=check_accessibility,
            check_activity=check_activity
        )
        verified_projects.append(verified)

    print(f"\n   Processed {len(verified_projects)} projects")

    # 统计结果
    valid_count = sum(1 for p in verified_projects if p.get('is_valid', True))
    invalid_count = len(verified_projects) - valid_count

    # 过滤
    print(f"\n[2/2] Filtering results...")
    valid_projects, invalid_projects = filter_valid_projects(verified_projects, remove_invalid=True)

    # 输出报告
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    print(f"Total projects:    {len(all_projects)}")
    print(f"Valid projects:    {len(valid_projects)}")
    print(f"Invalid projects:  {invalid_count}")
    print("=" * 60)

    if invalid_projects:
        print("\nInvalid projects (filtered out):")
        for p in invalid_projects[:10]:  # 只显示前10个
            notes = p.get('validation_notes', [])
            notes_str = '; '.join(notes) if notes else 'Unknown issue'
            print(f"  - {p.get('client', 'Unknown')}: {notes_str}")
        if len(invalid_projects) > 10:
            print(f"  ... and {len(invalid_projects) - 10} more")

    # 保存结果
    output_path = output_file or PROJECT_ROOT / "output" / "verified_projects.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        'verified_at': datetime.now().isoformat(),
        'total_projects': len(all_projects),
        'valid_projects': len(valid_projects),
        'invalid_projects': invalid_count,
        'check_accessibility': check_accessibility,
        'check_activity': check_activity,
        'projects': verified_projects
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_path}")
    return valid_projects


def run_verification(
    data_source: str = None,
    output_file: str = None,
    check_accessibility: bool = False,
    check_activity: bool = False
):
    """同步运行校验任务（不依赖异步 MCP）"""
    print("=" * 60)
    print("Project Data Verification (Sync Mode)")
    print("=" * 60)

    # 加载数据
    if data_source and Path(data_source).exists():
        with open(data_source, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_projects = data.get('projects', data)
        print(f"\nLoaded {len(all_projects)} projects from {data_source}")
    else:
        all_projects = load_research_data()
        print(f"\nLoaded {len(all_projects)} projects from process_design_projects.py")

    if not all_projects:
        print("ERROR: No projects found to verify")
        return []

    # 运行校验（同步版本）
    print(f"\n[1/2] Verifying {len(all_projects)} projects...")
    print("   - Email format validation")
    print("   - Link format validation")
    if check_accessibility:
        print("   - Link accessibility (simulated)")
    if check_activity:
        print("   - Project activity (simulated)")

    verified_projects = []
    for i, project in enumerate(all_projects, 1):
        client = project.get('client', 'Unknown')
        print(f"   [{i}/{len(all_projects)}] {client}", end='\r')

        verified = verify_project_sync(
            project,
            check_accessibility=check_accessibility,
            check_activity=check_activity
        )
        verified_projects.append(verified)

    print(f"\n   Processed {len(verified_projects)} projects")

    # 统计结果
    valid_count = sum(1 for p in verified_projects if p.get('is_valid', True))
    invalid_count = len(verified_projects) - valid_count

    # 过滤
    print(f"\n[2/2] Filtering results...")
    valid_projects, invalid_projects = filter_valid_projects(verified_projects, remove_invalid=True)

    # 输出报告
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    print(f"Total projects:    {len(all_projects)}")
    print(f"Valid projects:    {len(valid_projects)}")
    print(f"Invalid projects:  {invalid_count}")
    print("=" * 60)

    if invalid_projects:
        print("\nInvalid projects (filtered out):")
        for p in invalid_projects[:10]:
            notes = p.get('validation_notes', [])
            notes_str = '; '.join(notes) if notes else 'Unknown issue'
            print(f"  - {p.get('client', 'Unknown')}: {notes_str}")
        if len(invalid_projects) > 10:
            print(f"  ... and {len(invalid_projects) - 10} more")

    # 保存结果
    output_path = output_file or PROJECT_ROOT / "output" / "verified_projects.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        'verified_at': datetime.now().isoformat(),
        'total_projects': len(all_projects),
        'valid_projects': len(valid_projects),
        'invalid_projects': invalid_count,
        'check_accessibility': check_accessibility,
        'check_activity': check_activity,
        'projects': verified_projects
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_path}")
    return valid_projects


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Verify design project data validity'
    )
    parser.add_argument(
        '--data', '-d',
        help='Input data file (JSON)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path'
    )
    parser.add_argument(
        '--full-check',
        action='store_true',
        help='Include link accessibility and activity checks (requires MCP tools)'
    )
    parser.add_argument(
        '--async',
        action='store_true',
        dest='use_async',
        help='Use async mode with MCP tools'
    )

    args = parser.parse_args()

    if args.full_check and args.use_async:
        asyncio.run(run_verification_async(
            data_source=args.data,
            output_file=args.output,
            check_accessibility=True,
            check_activity=True
        ))
    else:
        run_verification(
            data_source=args.data,
            output_file=args.output,
            check_accessibility=args.full_check,
            check_activity=args.full_check
        )


if __name__ == "__main__":
    main()
