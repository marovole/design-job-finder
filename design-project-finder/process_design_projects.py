#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Design Projects Data Processor
处理从多个平台收集的设计项目数据，进行去重、评分、标准化和输出
"""

import csv
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


def normalize_company_name(name: str) -> str:
    """标准化公司名称，用于去重"""
    if not name:
        return ""

    # 移除常见公司后缀
    suffixes = [
        'Inc', 'Inc.', 'LLC', 'Ltd', 'Ltd.', 'Corporation', 'Corp', 'Corp.',
        'Limited', 'Company', 'Co', 'Co.', 'Group', 'Studio', 'Studios',
        '有限公司', '股份有限公司', '公司'
    ]

    result = name
    for suffix in suffixes:
        # 不区分大小写替换
        result = re.sub(rf'\b{re.escape(suffix)}\b', '', result, flags=re.IGNORECASE)

    # 移除特殊字符，只保留字母数字和空格
    result = re.sub(r'[^\w\s]', '', result)

    # 转小写并去除多余空格
    return ' '.join(result.lower().split())


def extract_keywords(text: str, max_words: int = 3) -> str:
    """从文本中提取关键词"""
    if not text:
        return ""

    # 移除常见停用词
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'need', 'needs'
    }

    # 分词并过滤
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]

    # 返回前N个关键词
    return '_'.join(keywords[:max_words])


def normalize_project_key(project: Dict) -> str:
    """生成项目唯一标识符"""
    company = normalize_company_name(project.get('客户名称', ''))
    title = extract_keywords(project.get('项目标题', ''))
    platform = project.get('数据来源', 'unknown')

    return f"{company}_{title}_{platform}".lower()


def has_more_contact_info(proj1: Dict, proj2: Dict) -> bool:
    """比较两个项目的联系信息完整度"""
    def count_contact_fields(proj):
        count = 0
        if proj.get('客户邮箱地址'): count += 3  # 邮箱权重最高
        if proj.get('客户LinkedIn链接'): count += 2
        if proj.get('公司网站'): count += 1
        return count

    return count_contact_fields(proj1) > count_contact_fields(proj2)


def is_duplicate(project: Dict, existing_projects: List[Dict]) -> Tuple[bool, Optional[int]]:
    """
    检查项目是否重复
    返回: (是否重复, 如果重复则返回应该被替换的项目索引)
    """
    key = normalize_project_key(project)

    for idx, existing in enumerate(existing_projects):
        existing_key = normalize_project_key(existing)
        if key == existing_key:
            # 如果新项目联系信息更完整，返回索引以便替换
            if has_more_contact_info(project, existing):
                return True, idx
            return True, None

    return False, None


def extract_budget_number(budget_str: str) -> float:
    """从预算字符串中提取数值（取平均值）"""
    if not budget_str:
        return 0.0

    # 处理各种格式: "$1000-2000", "1k-2k", "Fixed: $1500", "Up to $3000"
    # 移除货币符号和非数字字符（保留数字、点、逗号、k）
    cleaned = budget_str.lower().replace(',', '')

    # 提取所有数字（包括k表示的千）
    numbers = []

    # 匹配 "1k", "2.5k", "1000", "1,000" 等格式
    pattern = r'(\d+(?:\.\d+)?)\s*k'
    k_matches = re.findall(pattern, cleaned)
    for match in k_matches:
        numbers.append(float(match) * 1000)

    # 匹配普通数字
    pattern = r'(\d+(?:\.\d+)?)'
    num_matches = re.findall(pattern, cleaned.replace('k', ''))
    for match in num_matches:
        num = float(match)
        # 如果数字小于100，可能是千的单位
        if num > 100:
            numbers.append(num)

    if not numbers:
        return 0.0

    # 如果有多个数字，取平均值
    return sum(numbers) / len(numbers)


def extract_budget_range(budget_str: str) -> Tuple[float, float, float]:
    """
    提取预算范围
    返回: (下限, 上限, 中值)
    """
    if not budget_str:
        return 0.0, 0.0, 0.0

    cleaned = budget_str.lower().replace(',', '')

    # 提取所有数字
    numbers = []

    # 匹配 "1k", "2.5k" 等
    k_pattern = r'(\d+(?:\.\d+)?)\s*k'
    for match in re.findall(k_pattern, cleaned):
        numbers.append(float(match) * 1000)

    # 匹配普通数字
    num_pattern = r'(\d+(?:\.\d+)?)'
    cleaned_no_k = re.sub(k_pattern, '', cleaned)
    for match in re.findall(num_pattern, cleaned_no_k):
        num = float(match)
        if num > 100:
            numbers.append(num)

    if not numbers:
        return 0.0, 0.0, 0.0

    # 如果只有一个数字，认为是固定价格
    if len(numbers) == 1:
        return numbers[0], numbers[0], numbers[0]

    # 如果有多个数字，取最小和最大作为范围
    min_budget = min(numbers)
    max_budget = max(numbers)
    avg_budget = (min_budget + max_budget) / 2

    return min_budget, max_budget, avg_budget


def validate_email(email: str) -> str:
    """简单的邮箱格式验证"""
    if not email:
        return "无"

    # 基本的邮箱格式检查
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email.strip()):
        return "格式有效"
    return "格式无效"


def parse_date(date_str: str) -> Tuple[str, int]:
    """
    解析日期字符串
    返回: (标准化日期 YYYY-MM-DD, 距今天数)
    """
    if not date_str:
        return "", 999

    today = datetime.now()

    # 处理相对时间: "2 days ago", "1 week ago", "3 hours ago"
    date_str_lower = date_str.lower()

    if 'hour' in date_str_lower or 'hr' in date_str_lower:
        return today.strftime('%Y-%m-%d'), 0

    if 'day' in date_str_lower:
        match = re.search(r'(\d+)\s*day', date_str_lower)
        if match:
            days = int(match.group(1))
            date = today - datetime.timedelta(days=days)
            return date.strftime('%Y-%m-%d'), days

    if 'week' in date_str_lower:
        match = re.search(r'(\d+)\s*week', date_str_lower)
        if match:
            days = int(match.group(1)) * 7
            date = today - datetime.timedelta(days=days)
            return date.strftime('%Y-%m-%d'), days

    if 'month' in date_str_lower:
        match = re.search(r'(\d+)\s*month', date_str_lower)
        if match:
            days = int(match.group(1)) * 30
            date = today - datetime.timedelta(days=days)
            return date.strftime('%Y-%m-%d'), days

    # 尝试解析标准日期格式
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%Y']:
        try:
            date = datetime.strptime(date_str, fmt)
            days_diff = (today - date).days
            return date.strftime('%Y-%m-%d'), days_diff
        except:
            continue

    # 无法解析，返回原始字符串
    return date_str, 999


def calculate_priority_score(project: Dict) -> int:
    """
    计算项目优先级分数 (0-100)
    预算(40) + 联系方式(30) + 紧急度(15) + 客户质量(15)
    """
    score = 0

    # 预算权重 (40分)
    budget = extract_budget_number(project.get('项目预算范围', ''))
    if budget >= 2000:
        score += 40
    elif budget >= 1000:
        score += 30
    elif budget >= 500:
        score += 20
    else:
        score += min(budget / 50, 10)

    # 联系方式完整度 (30分)
    if project.get('客户邮箱地址'):
        score += 15
    if project.get('客户LinkedIn链接'):
        score += 10
    if project.get('公司网站'):
        score += 5

    # 项目紧急度 (15分)
    status = project.get('项目状态', '').lower()
    if '紧急' in status or 'urgent' in status:
        score += 15
    elif '立即' in status or 'immediate' in status or 'asap' in status:
        score += 10

    # 客户质量 (15分)
    client_type = project.get('客户类型', '').lower()
    if '大企业' in client_type or 'enterprise' in client_type:
        score += 15
    elif '中小企业' in client_type or '初创' in client_type or 'startup' in client_type or 'smb' in client_type:
        score += 10
    elif '个人' in client_type or 'individual' in client_type:
        score += 5

    return min(score, 100)


def determine_priority_label(score: int) -> str:
    """根据分数确定优先级标签"""
    if score >= 70:
        return "A级-极高优先"
    elif score >= 50:
        return "B级-高优先"
    elif score >= 30:
        return "C级-中优先"
    else:
        return "D级-低优先"


def clean_and_enrich_project(project: Dict) -> Dict:
    """清洗并丰富项目数据"""
    # 提取预算范围
    budget_str = project.get('项目预算范围', '')
    budget_min, budget_max, budget_avg = extract_budget_range(budget_str)

    project['预算下限USD'] = budget_min
    project['预算上限USD'] = budget_max
    project['预算中值USD'] = budget_avg

    # 解析时间
    date_str = project.get('发布时间', '')
    normalized_date, days_ago = parse_date(date_str)
    project['发布时间标准化'] = normalized_date
    project['距今天数'] = days_ago

    # 验证邮箱
    email = project.get('客户邮箱地址', '')
    project['邮箱有效性'] = validate_email(email)

    # 计算优先级
    score = calculate_priority_score(project)
    project['优先级分数'] = score
    project['优先级标签'] = determine_priority_label(score)

    # 确定推荐联系方式
    if email and validate_email(email) == "格式有效":
        project['推荐联系方式'] = "邮箱优先"
    elif project.get('客户LinkedIn链接'):
        project['推荐联系方式'] = "LinkedIn"
    elif project.get('平台项目链接'):
        project['推荐联系方式'] = "平台内联系"
    else:
        project['推荐联系方式'] = "需要进一步搜索"

    # 添加数据收集时间
    project['数据收集时间'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    return project


def deduplicate_projects(projects: List[Dict]) -> List[Dict]:
    """去重项目列表"""
    unique_projects = []

    for project in projects:
        is_dup, replace_idx = is_duplicate(project, unique_projects)

        if not is_dup:
            # 不是重复，直接添加
            unique_projects.append(project)
        elif replace_idx is not None:
            # 是重复，但新项目信息更完整，替换旧项目
            unique_projects[replace_idx] = project
        # 如果 is_dup=True 但 replace_idx=None，说明旧项目更好，跳过

    return unique_projects


def generate_csv_output(projects: List[Dict], output_file: str):
    """生成CSV文件"""
    if not projects:
        print("警告: 没有项目数据，跳过CSV生成")
        return

    # 定义CSV列顺序
    columns = [
        "优先级标签", "优先级分数", "数据来源",
        "项目标题", "项目详细要求", "设计类型标签", "项目状态",
        "项目预算范围", "预算下限USD", "预算上限USD", "预算中值USD",
        "客户名称", "客户类型", "客户所在行业", "客户信誉分数", "客户以往项目数",
        "客户邮箱地址", "邮箱有效性", "客户LinkedIn链接", "公司网站", "平台项目链接",
        "发布时间", "发布时间标准化", "距今天数",
        "是否已生成邮件", "邮件文件路径", "推荐联系方式",
        "数据收集时间", "备注"
    ]

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(projects)

    print(f"✓ CSV文件已生成: {output_file}")


def generate_contact_list(projects: List[Dict], output_file: str):
    """生成纯联系方式列表CSV"""
    if not projects:
        return

    # 只包含有联系方式的项目
    contacts = []
    for proj in projects:
        if proj.get('客户邮箱地址') or proj.get('客户LinkedIn链接') or proj.get('公司网站'):
            contacts.append({
                "优先级": proj.get('优先级标签', ''),
                "客户名称": proj.get('客户名称', ''),
                "客户类型": proj.get('客户类型', ''),
                "项目预算中值USD": proj.get('预算中值USD', 0),
                "邮箱地址": proj.get('客户邮箱地址', ''),
                "LinkedIn链接": proj.get('客户LinkedIn链接', ''),
                "公司网站": proj.get('公司网站', ''),
                "首选联系方式": proj.get('推荐联系方式', ''),
                "备注": proj.get('项目标题', '')[:50]
            })

    if not contacts:
        print("警告: 没有包含联系方式的项目")
        return

    columns = ["优先级", "客户名称", "客户类型", "项目预算中值USD",
               "邮箱地址", "LinkedIn链接", "公司网站", "首选联系方式", "备注"]

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(contacts)

    print(f"✓ 联系人列表已生成: {output_file} ({len(contacts)} 条记录)")


def generate_summary_report(projects: List[Dict], output_file: str):
    """生成统计摘要报告"""
    if not projects:
        print("警告: 没有项目数据，跳过报告生成")
        return

    total = len(projects)
    with_contact = sum(1 for p in projects if p.get('客户邮箱地址') or p.get('客户LinkedIn链接'))
    contact_rate = (with_contact / total * 100) if total > 0 else 0

    with_email = sum(1 for p in projects if p.get('是否已生成邮件') == '是')

    # 按优先级统计
    priority_stats = defaultdict(lambda: {'count': 0, 'budgets': [], 'contacts': 0})
    for proj in projects:
        priority = proj.get('优先级标签', 'D级-低优先')
        priority_stats[priority]['count'] += 1
        priority_stats[priority]['budgets'].append(proj.get('预算中值USD', 0))
        if proj.get('客户邮箱地址') or proj.get('客户LinkedIn链接'):
            priority_stats[priority]['contacts'] += 1

    # 按平台统计
    platform_stats = defaultdict(lambda: {'count': 0, 'budgets': [], 'contacts': 0})
    for proj in projects:
        platform = proj.get('数据来源', 'Unknown')
        platform_stats[platform]['count'] += 1
        platform_stats[platform]['budgets'].append(proj.get('预算中值USD', 0))
        if proj.get('客户邮箱地址') or proj.get('客户LinkedIn链接'):
            platform_stats[platform]['contacts'] += 1

    # 按客户类型统计
    client_type_stats = defaultdict(int)
    for proj in projects:
        client_type = proj.get('客户类型', 'Unknown')
        client_type_stats[client_type] += 1

    # 按预算分布
    budget_ranges = {
        '< $500': 0,
        '$500 - $1,000': 0,
        '$1,000 - $2,000': 0,
        '$2,000 - $5,000': 0,
        '> $5,000': 0
    }
    for proj in projects:
        budget = proj.get('预算中值USD', 0)
        if budget < 500:
            budget_ranges['< $500'] += 1
        elif budget < 1000:
            budget_ranges['$500 - $1,000'] += 1
        elif budget < 2000:
            budget_ranges['$1,000 - $2,000'] += 1
        elif budget < 5000:
            budget_ranges['$2,000 - $5,000'] += 1
        else:
            budget_ranges['> $5,000'] += 1

    # TOP 10 项目
    top_projects = sorted(projects, key=lambda p: p.get('优先级分数', 0), reverse=True)[:10]

    # 生成报告
    report = f"""# 设计项目收集报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**搜索范围**: 多个海外设计平台（Fiverr, Upwork, Dribbble等）

---

## 📊 数据概览

- **总项目数**: {total} 个
- **有效联系方式**: {with_contact} 个 ({contact_rate:.1f}%)
- **已生成营销邮件**: {with_email} 个

---

## 🎯 按优先级统计

| 优先级 | 项目数 | 平均预算 | 有联系方式 |
|--------|--------|----------|------------|
"""

    for priority in ["A级-极高优先", "B级-高优先", "C级-中优先", "D级-低优先"]:
        if priority in priority_stats:
            stat = priority_stats[priority]
            avg_budget = sum(stat['budgets']) / len(stat['budgets']) if stat['budgets'] else 0
            contact_pct = (stat['contacts'] / stat['count'] * 100) if stat['count'] > 0 else 0
            report += f"| {priority} | {stat['count']} | ${avg_budget:,.0f} | {stat['contacts']} ({contact_pct:.0f}%) |\n"

    report += f"""
---

## 🌐 按数据来源统计

| 平台 | 项目数 | 平均预算 | 有效联系率 |
|------|--------|----------|------------|
"""

    for platform, stat in sorted(platform_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        avg_budget = sum(stat['budgets']) / len(stat['budgets']) if stat['budgets'] else 0
        contact_pct = (stat['contacts'] / stat['count'] * 100) if stat['count'] > 0 else 0
        report += f"| {platform} | {stat['count']} | ${avg_budget:,.0f} | {contact_pct:.0f}% |\n"

    report += f"""
---

## 🏢 按客户类型统计

"""
    for client_type, count in sorted(client_type_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total * 100) if total > 0 else 0
        report += f"- **{client_type}**: {count} 个 ({pct:.0f}%)\n"

    report += f"""
---

## 📈 按预算分布

"""
    for range_name, count in budget_ranges.items():
        report += f"- **{range_name}**: {count} 个\n"

    report += f"""
---

## 🔥 重点推荐项目 (TOP 10)

"""

    for i, proj in enumerate(top_projects, 1):
        report += f"""
### {i}. {proj.get('项目标题', 'N/A')} - {proj.get('数据来源', 'N/A')}
- **客户**: {proj.get('客户名称', 'N/A')} ({proj.get('客户类型', 'N/A')})
- **预算**: ${proj.get('预算中值USD', 0):,.0f}
- **需求**: {proj.get('项目详细要求', 'N/A')[:100]}...
- **联系**: {'✉️ ' + proj.get('客户邮箱地址', '') if proj.get('客户邮箱地址') else ''} {'🔗 ' + proj.get('客户LinkedIn链接', '') if proj.get('客户LinkedIn链接') else ''}
- **优先级分数**: {proj.get('优先级分数', 0)}/100
"""

    report += f"""
---

## 📧 营销活动建议

### 本周行动计划
1. **立即联系 (今天)**: {priority_stats.get('A级-极高优先', {}).get('count', 0)} 个 A级项目
2. **本周跟进**: {priority_stats.get('B级-高优先', {}).get('count', 0)} 个 B级项目
3. **下周触达**: {priority_stats.get('C级-中优先', {}).get('count', 0)} 个 C级项目

### 推荐策略
- **A级项目**: 直接邮件 + LinkedIn InMail 双渠道
- **B级项目**: 邮件为主,准备定制化案例
- **C级项目**: 批量邮件,标准化模板

### 预期转化率
- 假设响应率 10%: ~{int(with_contact * 0.1)} 个潜在对话
- 假设转化率 30%: ~{int(with_contact * 0.1 * 0.3)} 个新订阅客户

---

## 📝 下一步行动

- [ ] 审核自动生成的营销邮件
- [ ] 为 A级项目准备定制化案例研究
- [ ] 设置 CRM 跟踪所有外联活动
- [ ] 两周后重新运行搜索(新项目)
- [ ] 分析响应率并优化邮件模板

---

**报告生成**: design-project-finder v1.0
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 统计报告已生成: {output_file}")


def process_projects(raw_projects: List[Dict], output_dir: str = 'output'):
    """
    主处理流程

    Args:
        raw_projects: 从研究报告中提取的原始项目列表
        output_dir: 输出目录
    """
    import os

    print(f"\n开始处理 {len(raw_projects)} 个项目...")

    # 1. 清洗和丰富数据
    print("\n[1/5] 清洗和丰富数据...")
    enriched = [clean_and_enrich_project(p) for p in raw_projects]
    print(f"✓ 数据清洗完成")

    # 2. 去重
    print("\n[2/5] 去重...")
    unique = deduplicate_projects(enriched)
    duplicate_count = len(enriched) - len(unique)
    print(f"✓ 去重完成，移除 {duplicate_count} 个重复项目")

    # 3. 排序（按优先级分数降序）
    print("\n[3/5] 排序...")
    sorted_projects = sorted(unique, key=lambda p: p.get('优先级分数', 0), reverse=True)
    print(f"✓ 排序完成")

    # 4. 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 5. 生成输出文件
    print("\n[4/5] 生成输出文件...")

    timestamp = datetime.now().strftime('%Y-%m-%d')

    csv_file = os.path.join(output_dir, f'design_projects_{timestamp}.csv')
    generate_csv_output(sorted_projects, csv_file)

    contact_file = os.path.join(output_dir, 'contact_list.csv')
    generate_contact_list(sorted_projects, contact_file)

    summary_file = os.path.join(output_dir, 'design_projects_summary.md')
    generate_summary_report(sorted_projects, summary_file)

    # 6. 打印统计摘要
    print("\n[5/5] 处理完成!")
    print("\n" + "="*60)
    print(f"总项目数: {len(raw_projects)}")
    print(f"去重后: {len(unique)}")
    print(f"A级项目: {sum(1 for p in sorted_projects if p.get('优先级标签') == 'A级-极高优先')}")
    print(f"B级项目: {sum(1 for p in sorted_projects if p.get('优先级标签') == 'B级-高优先')}")
    print(f"有效联系方式: {sum(1 for p in sorted_projects if p.get('客户邮箱地址') or p.get('客户LinkedIn链接'))}")
    print("="*60)

    return sorted_projects


# 示例用法
if __name__ == "__main__":
    # 这是一个示例，实际使用时需要从研究报告中提取数据
    sample_projects = [
        {
            "数据来源": "Upwork",
            "项目标题": "SaaS Dashboard Redesign",
            "项目详细要求": "Need a complete redesign of our SaaS platform dashboard with modern UI/UX",
            "项目预算范围": "$2000-3500",
            "项目状态": "Urgent - Need to start immediately",
            "客户名称": "TechStartup Inc",
            "客户类型": "初创公司",
            "客户所在行业": "SaaS/B2B",
            "客户邮箱地址": "john@techstartup.com",
            "客户LinkedIn链接": "linkedin.com/in/john",
            "公司网站": "techstartup.com",
            "发布时间": "2 days ago"
        }
    ]

    # 处理项目
    processed = process_projects(sample_projects)
    print(f"\n处理完成! 输出文件在 output/ 目录")
