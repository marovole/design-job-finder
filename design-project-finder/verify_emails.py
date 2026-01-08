#!/usr/bin/env python3
"""
Email Verification Script - Design Project Finder Skill
验证所有营销邮件中的占位符已被正确替换
"""

import re
import os
from pathlib import Path

# 默认邮件目录 - 支持新旧结构
# 优先检查 output/latest/marketing_emails（新结构）
# 降级检查 output/marketing_emails（旧结构）
DEFAULT_EMAIL_DIR = Path("output/latest/marketing_emails")
FALLBACK_EMAIL_DIR = Path("output/marketing_emails")

def find_email_dir():
    """自动查找邮件目录（支持新旧结构）"""
    if DEFAULT_EMAIL_DIR.exists():
        return DEFAULT_EMAIL_DIR
    elif FALLBACK_EMAIL_DIR.exists():
        return FALLBACK_EMAIL_DIR
    return None

def verify_emails(email_dir=None):
    """
    验证所有邮件文件没有未替换的占位符

    Returns:
        bool: True 表示所有邮件都正确, False 表示存在问题
    """
    if email_dir is None:
        # 自动查找邮件目录
        email_dir = find_email_dir()
        if email_dir is None:
            print(f"❌ 未找到邮件目录")
            print("   尝试查找: output/latest/marketing_emails/ (新结构)")
            print("   或: output/marketing_emails/ (旧结构)")
            return False
    else:
        email_dir = Path(email_dir)

    # 占位符模式: {variable_name}
    placeholder_pattern = r'\{[a-zA-Z_][a-zA-Z0-9_]*\}'

    issues = []
    total_files = 0
    verified_files = 0

    if not email_dir.exists():
        print(f"❌ 邮件目录不存在: {email_dir}")
        return False

    for root, dirs, files in os.walk(email_dir):
        for file in files:
            if file.endswith('.md'):
                total_files += 1
                filepath = Path(root) / file

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(placeholder_pattern, content)

                    # 排除合法的大括号内容（如 {industry} 是占位符，但 Markdown 链接可能合法）
                    # 过滤掉合法的 Markdown 语法
                    filtered_matches = []
                    for match in matches:
                        # 跳过 Markdown 链接中的文本 [text](url)
                        # 以及常见的 Markdown 语法
                        if match in ['{self}', '{title}', '{description}']:
                            continue
                        filtered_matches.append(match)

                    if filtered_matches:
                        unique_matches = list(set(filtered_matches))
                        issues.append({
                            'file': str(filepath.relative_to(Path.cwd())),
                            'placeholders': unique_matches
                        })
                    else:
                        verified_files += 1

    print("=" * 60)
    print("📧 邮件内容验证报告")
    print("=" * 60)

    if total_files == 0:
        print("⚠️  没有找到任何邮件文件")
        return False

    if issues:
        print(f"❌ 发现 {len(issues)} 个邮件存在问题:\n")
        for issue in issues:
            print(f"  📄 {issue['file']}")
            print(f"     未替换的占位符: {', '.join(issue['placeholders'])}")
            print()
        print("-" * 60)
        print("修复建议:")
        print("  1. 检查 process_design_projects.py 中的 generate_email_content() 函数")
        print("  2. 确保所有字符串使用 f-string 格式: f\"...{variable}...\"")
        print("  3. 重新运行: python3 process_design_projects.py")
        print("  4. 重新验证: python3 verify_emails.py")
        print("=" * 60)
        return False
    else:
        print(f"✅ 验证通过!")
        print(f"   - 总邮件数: {total_files}")
        print(f"   - 全部通过: {verified_files}")
        print(f"   - 无占位符残留")
        print("=" * 60)
        print("\n🚀 邮件已准备就绪，可以用于营销推广！")
        return True

def verify_with_grep():
    """使用 grep 命令快速验证（备用方法）"""
    print("\n🔍 使用 grep 快速验证...")

    # 支持新旧结构
    email_dir = find_email_dir()
    if email_dir is None:
        email_dir = Path("output/marketing_emails")

    patterns = ['{industry}', '{title}', '{client}', '{budget}']
    found_issues = False

    for pattern in patterns:
        result = os.popen(f'grep -r "{pattern}" "{email_dir}/" 2>/dev/null').read()
        if result.strip():
            found_issues = True
            print(f"  ❌ 发现: {pattern}")
            print(result.strip()[:200])

    if not found_issues:
        print("  ✅ 未发现占位符")

def main():
    """主函数"""
    import sys

    # 支持命令行参数
    email_dir = sys.argv[1] if len(sys.argv) > 1 else None

    print("\n🎯 Design Project Finder - 邮件验证工具")
    print("-" * 60)

    # 方法1: Python 验证（推荐）
    result = verify_emails(email_dir)

    # 方法2: grep 验证（备用）
    verify_with_grep()

    # 返回退出码
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
