#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Marketing Email Generator
为设计项目生成个性化营销邮件
"""

import os
import re
from typing import Dict, List
from datetime import datetime


def select_tone(project: Dict, user_preference: str = "自适应") -> str:
    """
    根据客户类型选择邮件语气

    Args:
        project: 项目数据
        user_preference: 用户偏好 (专业正式/友好亲切/创意活泼/自适应)

    Returns:
        邮件语气描述
    """
    if user_preference != "自适应":
        tone_map = {
            "专业正式": "professional and formal",
            "友好亲切": "friendly and warm",
            "创意活泼": "creative and energetic"
        }
        return tone_map.get(user_preference, "professional and warm")

    # 自适应：根据客户类型
    client_type = project.get('客户类型', '').lower()

    if '大企业' in client_type or 'enterprise' in client_type:
        return "professional and formal"
    elif '初创' in client_type or 'startup' in client_type:
        return "friendly and warm"
    elif '个人' in client_type or 'individual' in client_type:
        return "creative and energetic"
    else:
        # 默认：专业但友好
        return "professional and warm"


def generate_subject_lines(project: Dict) -> List[str]:
    """
    生成3个备选主题行

    Args:
        project: 项目数据

    Returns:
        3个主题行列表
    """
    project_type = project.get('设计类型标签', 'design project')
    client_name = project.get('客户名称', 'your company')
    industry = project.get('客户所在行业', '')

    subjects = [
        f"Re: Your {project_type} project - A flexible approach",
        f"Unlimited design for {client_name}",
        f"A different way to approach your {project_type} needs"
    ]

    # 如果有行业信息，添加行业相关主题
    if industry:
        subjects.append(f"Design subscription for {industry} businesses")

    return subjects[:3]


def generate_email_prompt(project: Dict, tone: str) -> str:
    """
    生成邮件生成的 LLM Prompt

    Args:
        project: 项目数据
        tone: 邮件语气

    Returns:
        完整的 prompt 字符串
    """
    platform = project.get('数据来源', 'a freelance platform')
    project_title = project.get('项目标题', 'design project')
    project_details = project.get('项目详细要求', '')
    budget = project.get('项目预算范围', 'your budget')
    client_type = project.get('客户类型', '')
    industry = project.get('客户所在行业', '')

    prompt = f"""You are a design consultant at designsub.studio writing a personalized outreach email to a potential client.

**Client's Project Information**:
- Platform: {platform}
- Project Title: {project_title}
- Detailed Requirements: {project_details}
- Budget Range: {budget}
- Client Type: {client_type}
- Industry: {industry}

**About designsub.studio**:
We are a design subscription service offering:
- Unlimited design requests and revisions
- Average 48-hour turnaround for initial drafts
- Fixed monthly fee, no hidden costs
- Professional UI/UX, branding, and web design team
- Pause or cancel anytime
- Perfect for teams needing ongoing design support

**Your Task**:
Write a {tone} outreach email (150-200 words) in English.

**Email Structure**:

1. **Opening** (2-3 sentences):
   - Mention you saw their project on {platform}
   - Show genuine understanding of their specific needs
   - Create interest without being pushy

2. **Value Proposition** (3-4 sentences):
   - Address their specific pain points
   - Explain how design subscription solves their needs
   - Examples:
     * For startups → emphasize cost control and flexibility
     * For tight budgets → emphasize value and unlimited revisions
     * For diverse needs → emphasize unlimited requests and fast delivery

3. **Call to Action** (2 sentences):
   - Invite a brief conversation or offer to share case studies
   - Provide clear next steps

**Requirements**:
- Length: 150-200 words
- Tone: {tone}
- Avoid: Template language, over-selling, empty promises
- Demonstrate: Professionalism, genuine understanding, sincerity
- Naturally integrate designsub.studio (don't force it)
- Write in English (for international clients)

Output only the email body, without subject line or signature.
"""

    return prompt


def generate_personalized_email(project: Dict, tone: str = None) -> str:
    """
    生成个性化邮件正文

    注意: 这是一个占位符函数。实际使用时需要调用 LLM API
    在 Claude Code 技能中，你应该使用 Claude 或其他 LLM 来生成邮件

    Args:
        project: 项目数据
        tone: 邮件语气（如果为 None 则自动选择）

    Returns:
        邮件正文
    """
    if tone is None:
        tone = select_tone(project)

    prompt = generate_email_prompt(project, tone)

    # TODO: 实际实现中，这里应该调用 LLM API
    # 例如使用 Claude API, OpenAI API, 或在 Claude Code 中直接使用 Anthropic SDK

    # 临时示例：返回一个模板化的邮件
    platform = project.get('数据来源', 'the platform')
    project_title = project.get('项目标题', 'your design project')
    client_name = project.get('客户名称', 'there')

    example_email = f"""Hi {client_name},

I noticed your {project_title} project on {platform}. Your requirements caught my attention, especially the focus on creating a modern, user-friendly design that aligns with your brand vision.

Many teams we work with face a similar challenge: they need ongoing design support, but hiring full-time or working with traditional agencies creates budget uncertainty and timeline bottlenecks. That's why we built designsub.studio as a design subscription service.

Instead of project-by-project pricing, you get unlimited design requests and revisions for a flat monthly fee. For your needs, this means you can tackle your current project, then seamlessly move to marketing materials, additional screens, or other design needs—all without renegotiating scope or budget.

We typically deliver initial concepts within 48 hours and work iteratively until you're completely satisfied. You can pause or cancel anytime, so there's no long-term commitment.

Would you be open to a quick 15-minute call this week to discuss your project? I'd love to share some relevant case studies and see if this approach might work for you.

Best regards,
[Your Name]
Design Consultant, designsub.studio
[Calendar Link] | [Portfolio]

---
**NOTE**: This is a template email. In production, replace this with actual LLM-generated content using the prompt above.
"""

    return example_email.strip()


def create_email_file(project: Dict, email_body: str, subject_lines: List[str],
                      output_dir: str, priority: str) -> str:
    """
    创建邮件 Markdown 文件

    Args:
        project: 项目数据
        email_body: 邮件正文
        subject_lines: 主题行列表
        output_dir: 输出目录
        priority: 优先级（用于确定子目录）

    Returns:
        保存的文件路径
    """
    # 确定子目录
    if priority in ['A级-极高优先', 'B级-高优先']:
        subdir = 'high_priority'
    else:
        subdir = 'medium_priority'

    # 创建目录
    full_dir = os.path.join(output_dir, 'marketing_emails', subdir)
    os.makedirs(full_dir, exist_ok=True)

    # 生成文件名（安全化客户名称）
    client_name = project.get('客户名称', 'Unknown')
    safe_name = re.sub(r'[^\w\s-]', '', client_name).strip().replace(' ', '_')
    project_num = project.get('项目编号', '000')
    filename = f"project_{project_num}_{safe_name}_email.md"
    filepath = os.path.join(full_dir, filename)

    # 生成 Markdown 内容
    content = f"""# Marketing Email - {client_name}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Priority**: {priority}
**Platform**: {project.get('数据来源', 'N/A')}

---

## Project Summary

- **Title**: {project.get('项目标题', 'N/A')}
- **Budget**: {project.get('项目预算范围', 'N/A')} (${project.get('预算中值USD', 0):,.0f} avg)
- **Client Type**: {project.get('客户类型', 'N/A')}
- **Industry**: {project.get('客户所在行业', 'N/A')}
- **Contact**:
  - Email: {project.get('客户邮箱地址', 'N/A')}
  - LinkedIn: {project.get('客户LinkedIn链接', 'N/A')}
  - Website: {project.get('公司网站', 'N/A')}

---

## Subject Lines (Choose One)

1. {subject_lines[0] if len(subject_lines) > 0 else 'N/A'}
2. {subject_lines[1] if len(subject_lines) > 1 else 'N/A'}
3. {subject_lines[2] if len(subject_lines) > 2 else 'N/A'}

---

## Email Body

{email_body}

---

## Notes

- [ ] Review and personalize if needed
- [ ] Add your name and contact info in signature
- [ ] Check all links work
- [ ] Send from professional email address
- [ ] Track response in CRM

**Recommended Contact Method**: {project.get('推荐联系方式', 'N/A')}
"""

    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def generate_emails_for_projects(projects: List[Dict], output_dir: str = 'output',
                                  tone_preference: str = "自适应",
                                  only_high_priority: bool = True) -> Dict[str, int]:
    """
    为项目批量生成营销邮件

    Args:
        projects: 项目列表
        output_dir: 输出目录
        tone_preference: 语气偏好
        only_high_priority: 是否只为 A/B 级项目生成邮件

    Returns:
        统计信息字典
    """
    print(f"\n开始生成营销邮件...")

    stats = {
        'total_projects': len(projects),
        'emails_generated': 0,
        'high_priority': 0,
        'medium_priority': 0
    }

    for i, project in enumerate(projects, 1):
        priority = project.get('优先级标签', 'D级-低优先')

        # 如果只处理高优先级，跳过低优先级项目
        if only_high_priority and priority not in ['A级-极高优先', 'B级-高优先']:
            continue

        print(f"\n[{i}/{len(projects)}] 生成邮件: {project.get('客户名称', 'N/A')} ({priority})")

        # 选择语气
        tone = select_tone(project, tone_preference)
        print(f"  语气: {tone}")

        # 生成主题行
        subject_lines = generate_subject_lines(project)

        # 生成邮件正文
        try:
            email_body = generate_personalized_email(project, tone)
            print(f"  ✓ 邮件正文已生成")
        except Exception as e:
            print(f"  ✗ 生成失败: {e}")
            continue

        # 保存到文件
        project['项目编号'] = f"{i:03d}"
        try:
            filepath = create_email_file(project, email_body, subject_lines,
                                        output_dir, priority)
            print(f"  ✓ 已保存: {filepath}")

            # 更新项目数据
            project['是否已生成邮件'] = '是'
            project['邮件文件路径'] = filepath

            stats['emails_generated'] += 1
            if priority in ['A级-极高优先', 'B级-高优先']:
                stats['high_priority'] += 1
            else:
                stats['medium_priority'] += 1

        except Exception as e:
            print(f"  ✗ 保存失败: {e}")
            project['是否已生成邮件'] = '否'

    print("\n" + "="*60)
    print(f"邮件生成完成!")
    print(f"总项目数: {stats['total_projects']}")
    print(f"已生成邮件: {stats['emails_generated']}")
    print(f"  - 高优先级: {stats['high_priority']}")
    print(f"  - 中优先级: {stats['medium_priority']}")
    print("="*60)

    return stats


def create_batch_template(output_dir: str = 'output'):
    """
    创建批量邮件发送模板说明文档
    """
    template_path = os.path.join(output_dir, 'marketing_emails', 'email_batch_template.md')
    os.makedirs(os.path.dirname(template_path), exist_ok=True)

    content = """# 批量邮件发送指南

## 📧 发送前检查清单

- [ ] 所有邮件已人工审核并个性化
- [ ] 签名中包含真实姓名和联系方式
- [ ] 所有链接（日历链接、作品集等）有效
- [ ] 使用正规商业邮箱（避免 Gmail/个人邮箱）
- [ ] 设置好邮件跟踪（打开率、回复率）
- [ ] CRM 已准备好记录所有外联活动

## 📅 推荐发送计划

### 第1周: A级项目（高优先级）

**Day 1-2**: 发送 5-10 封邮件
- 选择最高分的 A级项目
- 每封邮件间隔至少 1 小时
- 发送时间: 上午 9-11点 或 下午 2-4点（目标时区）

**Day 3-5**: 跟进 + 新发送
- 跟进未回复的邮件（2-3天后）
- 继续发送剩余 A级项目

### 第2周: B级项目 + A级跟进

**Day 6-10**: B级项目首次外联
- 每天 8-12 封
- 使用相同的策略

**Day 11-12**: 第二轮跟进
- 对所有未回复的 A/B级项目发送跟进邮件

### 第3周: C级项目（可选）

- 使用更标准化的模板
- 可以批量发送（每天 15-20 封）

## ✉️ 发送技巧

### 1. 个性化每封邮件
即使使用模板，也要确保：
- 提到具体的项目需求
- 使用客户的真实名字
- 引用他们的公司/产品

### 2. 避免垃圾邮件过滤器
- 不要使用全大写字母
- 避免过多的感叹号！！！
- 不要在邮件中放置太多链接
- 使用纯文本或简单 HTML（避免花哨格式）

### 3. 发送时机
**最佳发送时间** (以客户所在时区为准):
- 周二-周四 上午 9-11点
- 周二-周四 下午 2-4点
- 避免周一早晨和周五下午
- 避免节假日

### 4. 跟进策略
**第一次跟进** (2-3天后):
```
Subject: Re: [Original Subject]

Hi [Name],

Just wanted to follow up on my previous email about your [project]. I understand you're likely busy, but I'd love to discuss how designsub.studio could help with your design needs.

Would next week work for a quick 10-minute call?

Best,
[Your Name]
```

**第二次跟进** (1周后):
```
Subject: Final follow-up: [Project Name]

Hi [Name],

I wanted to reach out one last time about your [project]. If now isn't the right time, I completely understand.

If you'd like to explore design subscription in the future, feel free to reach out anytime.

Best of luck with your project!
[Your Name]
```

## 📊 跟踪指标

### 必须跟踪的数据:
- **发送数量**: 每天发送了多少封
- **打开率**: 多少人打开了邮件
- **响应率**: 多少人回复了
- **会议预约**: 多少次对话/演示
- **转化率**: 多少人成为付费客户

### 推荐工具:
- **邮件跟踪**: Mailtrack, HubSpot, Streak
- **CRM**: Airtable, Notion, HubSpot, Pipedrive
- **日历预约**: Calendly, Cal.com

## ⚠️ 注意事项

1. **遵守反垃圾邮件法律**
   - 包含退订链接（如适用）
   - 不要购买邮件列表
   - 尊重"不感兴趣"的回复

2. **保护客户隐私**
   - 不要公开分享客户联系信息
   - 安全存储所有数据
   - 遵守 GDPR/数据保护法规

3. **质量>数量**
   - 10 封精心撰写的邮件 > 50 封模板邮件
   - 专注于最有可能转化的 A/B级项目
   - 持续优化邮件模板

## 🎯 预期结果

基于行业基准:
- **打开率**: 25-35%
- **响应率**: 8-12%
- **会议预约率**: 3-5%
- **最终转化率**: 20-30% (从会议到付费客户)

例: 发送 50 封邮件
→ 12-15 人打开
→ 4-6 人回复
→ 2-3 次会议
→ 1 个新客户

## 📝 模板变体

### 变体 A: 直接价值
聚焦于解决客户问题，快速提及订阅模式

### 变体 B: 案例驱动
分享相关案例研究，展示结果

### 变体 C: 问题导向
以问题开头，引发思考

**建议**: A/B 测试不同变体，找到最有效的方式

---

**Created by**: design-project-finder v1.0
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
"""

    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 批量发送指南已创建: {template_path}")


# 示例用法
if __name__ == "__main__":
    # 示例项目数据
    sample_projects = [
        {
            "项目标题": "SaaS Dashboard Redesign",
            "项目详细要求": "Complete redesign of dashboard with modern UI/UX",
            "项目预算范围": "$2000-3500",
            "预算中值USD": 2750,
            "客户名称": "TechStartup Inc",
            "客户类型": "初创公司",
            "客户所在行业": "SaaS/B2B",
            "设计类型标签": "UI/UX Design",
            "数据来源": "Upwork",
            "优先级标签": "A级-极高优先",
            "优先级分数": 85,
            "客户邮箱地址": "john@techstartup.com",
            "客户LinkedIn链接": "linkedin.com/in/john",
            "公司网站": "techstartup.com",
            "推荐联系方式": "邮箱优先"
        }
    ]

    # 生成邮件
    stats = generate_emails_for_projects(sample_projects)
    create_batch_template()

    print("\n所有邮件已生成!")
