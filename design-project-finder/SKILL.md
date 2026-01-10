---
name: design-project-finder
description: "搜索海外设计工作平台,找到与用户专长匹配的项目,生成个性化营销邮件"
version: "2.0.0"
---

# 设计项目与客户搜索器 (Design Project Finder) v2.0

> **一键执行**: `python3 process_design_projects.py`
>
> **带增强验证**: `python3 process_design_projects.py --realtime-verify`
>
> **生成AI邮件**: `python3 process_design_projects.py --generate-emails`
>
> **完整模式**: `python3 process_design_projects.py --full`

---

## 🆕 v2.0 新功能

### 增强验证系统
- **多层邮箱验证**: 格式 → MX记录 → 一次性邮箱检测 → SMTP
- **智能URL验证**: LinkedIn专用格式验证 + 异步可达性检测 + 缓存
- **实时验证**: 数据收集时即验证，不再事后处理

### 深度个性化邮件
- **项目需求分析**: 自动提取技术需求、推断痛点、检测项目阶段
- **成就智能匹配**: 多维度匹配用户作品集与项目需求
- **推销角度优化**: 根据匹配结果确定最佳推销角度

---

## 用户背景

| 属性 | 值 |
|------|-----|
| **姓名** | 黄蓉 (Huang Rong) |
| **定位** | 资深 UX 设计师 / 产品经理 |
| **经验** | 10+ 年，华为 6 年 |
| **网站** | https://hueshadow.com |
| **邮箱** | hueshadow989@gmail.com |
| **LinkedIn** | https://www.linkedin.com/in/ronn-huang-7b50273a3/ |

### 核心专长 (用于项目匹配)
- B2B/SaaS 产品设计 (dashboard, analytics, admin)
- 企业级复杂系统 UX
- 设计系统 & 组件库

### 亮点项目 (用于邮件引用)

| 项目 | 对标 | 成果 |
|------|------|------|
| **HUAWEI Analytics** | Google Analytics | 21,000+ 应用全球接入 |
| **Business Connect** | Google My Business | 594 万商家 |
| **华为云费用中心** | - | 企业级云服务 |

### 优先行业
SaaS, B2B, Data Analytics, FinTech, Enterprise Software, Cloud Services

---

## 快速开始

### 执行流程

```bash
# 1. 运行数据处理脚本
python3 process_design_projects.py

# 2. 查看结果
output/latest/
├── projects_for_ai_emails_*.json  # AI邮件数据 (含匹配度)
├── design_projects_*.csv          # 完整项目数据
├── contact_list_*.csv             # 联系方式
└── marketing_emails/
    ├── ai_generated/              # Claude生成的个性化邮件
    └── high_priority/             # 模板邮件
```

### 输出示例

```
============================================================
SUMMARY
============================================================
User profile:      黄蓉
Total projects:    99
Valid projects:    95 (4 filtered)
High priority:     64
High match:        24 (基于您的专长)
With email:        68
============================================================
```

---

## 完整工作流程

### 阶段1: 数据收集 (可选 - 使用 Exa AI)

如需实时获取最新项目，使用 Exa 深度研究：

```python
# 启动研究任务
task_id = mcp__exa__deep_researcher_start(
    instructions="""
    搜索 {平台} 上正在寻找 UI/UX 设计师的活跃项目。

    对于每个项目提取:
    - 项目标题、客户名称、预算范围
    - 项目详细要求 (100-200字)
    - 客户邮箱、LinkedIn、公司网站
    - 客户类型、行业

    重点关注: dashboard, analytics, B2B, SaaS, enterprise 相关项目
    """,
    model="exa-research-pro"
)

# 轮询结果
result = mcp__exa__deep_researcher_check(taskId=task_id)
```

**目标平台**:
- Toptal, Upwork, Freelancer, Guru
- Dribbble, Behance, 99designs, Designhill
- LinkedIn, AngelList, We Work Remotely

### 阶段2: 数据处理

运行 `python3 process_design_projects.py`:

1. **加载用户配置** → `user_profile.yaml`
2. **数据去重** → 基于 客户名+标题关键词
3. **优先级评分** → 预算(35%) + 联系方式(25%) + 客户质量(20%) + 稳定性(20%)
4. **匹配度评分** → 基于用户专长关键词、行业、客户类型
5. **输出 JSON** → 包含 `match_score` 和 `recommended_highlight`

### 阶段2.5: 数据校验 (自动/增强)

#### 增强验证模式 (v2.0 推荐)

使用 `--realtime-verify` 启用多层验证：

```bash
python3 process_design_projects.py --realtime-verify --verification-level standard
```

**验证级别：**
| 级别 | 邮箱检查 | URL检查 | 速度 |
|------|---------|--------|------|
| `quick` | 仅格式 | 仅格式 | 最快 |
| `standard` | 格式+MX+一次性检测 | 格式+LinkedIn验证 | 推荐 |
| `full` | 全部+SMTP | 全部+可达性 | 较慢 |

#### 增强验证配置

```python
# 新版配置 (process_design_projects.py)
VERIFICATION_CONFIG = {
    'enabled': True,              # 启用校验
    'use_enhanced': True,         # 使用增强v2.0验证
    'check_email_format': True,   # 邮箱格式验证
    'check_email_mx': True,       # MX记录验证（新）
    'check_disposable': True,     # 一次性邮箱检测（新）
    'check_email_exists': False,  # SMTP验证（慢，默认关闭）
    'check_link_format': True,    # URL格式验证
    'check_accessibility': False, # HTTP可达性验证（慢）
    'remove_invalid': False,      # 保留所有项目，标记无效
    'verification_level': 'standard',  # quick/standard/full
}
```

#### 多层邮箱验证流程

```
Tier 1: 格式验证 (正则匹配)
    ↓ 通过
Tier 2: MX记录验证 (域名有邮件服务器配置)
    ↓ 通过
Tier 3: 一次性邮箱检测 (黑名单域名匹配)
    ↓ 通过
Tier 4: SMTP验证 (RCPT TO命令，可选)
    ↓ 通过
✓ 邮箱有效
```

**一次性邮箱检测：**
- 内置 150+ 常见一次性邮箱域名
- 支持自定义域名列表 (`disposable_domains.txt`)
- 自动识别可疑模式 (temp*, throwaway*, etc.)

#### 旧版验证配置（兼容）

```python
# 旧版配置
VERIFICATION_CONFIG = {
    'enabled': True,              # 启用校验
    'check_email_format': True,   # 邮箱格式验证
    'check_email_exists': True,   # 邮箱存在性验证 (SMTP)
    'check_link_format': True,    # 链接格式验证
    'check_accessibility': False, # 链接可访问性（慢，需Playwright MCP）
    'check_activity': False,      # 项目活跃度（慢，需Exa AI MCP）
    'remove_invalid': False       # 保留所有项目，标记无效项目
}
```

**校验内容：**
- 邮箱格式验证 (正则表达式)
- 邮箱存在性验证 (SMTP 握手，无需 API)
- URL 格式验证 (website, linkedin, platform_link)
- 链接可访问性验证 (可选，使用 Playwright MCP)
- 项目活跃度验证 (可选，使用 Exa AI 搜索)

**CSV 输出字段：**
| 字段 | 说明 |
|------|------|
| `是否有效` | 格式校验是否通过 |
| `完全验证通过` | 网站可访问 + 邮箱存在 |
| `网站可访问` | 是/否/未知 |
| `网站标题` | 页面标题 |
| `邮箱格式正确` | 是/否 |
| `邮箱存在` | 是/否/未知 |
| `校验备注` | 校验问题列表 |
| `校验时间` | 校验时间戳 |

**SMTP 邮箱验证说明：**
- 通过 SMTP RCPT TO 命令验证邮箱是否存在
- 无需 API key，完全免费
- 可能被部分邮件服务器拒绝（会标记为"未知"）

### 阶段3: AI 邮件生成

Claude 读取 JSON 并为高匹配项目生成个性化邮件。

---

## 匹配度评分算法

```python
def calculate_match_score(project, user_profile):
    score = 0

    # 关键词匹配 (40分)
    high_keywords = ['dashboard', 'analytics', 'admin', 'b2b', 'saas', 'enterprise']
    if any(kw in project_text for kw in high_keywords):
        score += 30

    # 行业匹配 (30分)
    if industry in ['SaaS', 'B2B', 'FinTech', 'Data Analytics']:
        score += 30

    # 客户类型匹配 (20分)
    if client_type in ['Enterprise', 'SME']:
        score += 20

    # 预算匹配 (10分)
    if budget >= 2000:
        score += 10

    return min(score, 100)
```

---

## 个性化邮件生成策略

### 根据项目类型选择开场白

**Dashboard/Analytics** (关键词: dashboard, analytics, data):
```
During my 6 years at Huawei, I led the UX design for HUAWEI Analytics—
a platform benchmarked against Google Analytics that now serves 21,000+
apps globally. Your {project} aligns closely with my expertise.
```

**B2B/SaaS** (关键词: b2b, saas, enterprise, admin):
```
I've spent 6 years specializing in enterprise B2B product design at Huawei,
including cloud billing systems and developer consoles. Complex system
architecture is my strength—exactly what your {project} requires.
```

**商家管理** (关键词: merchant, business, commerce):
```
I led the design for Business Connect (Huawei's Google My Business),
which now serves 5.94 million merchants. Your {project} resonates
strongly with my merchant platform experience.
```

**通用开场**:
```
With 10+ years in UX design including 6 years at Huawei working on
enterprise platforms serving millions of users, I bring deep expertise
in user-centered design and complex system thinking.
```

### 邮件结构

```markdown
**开场 (2-3句)**
- 提及在 {platform} 看到 {title}
- 引用 recommended_highlight 展示相关经验
- 用具体数据建立可信度

**价值主张 (3-4句)**
- Enterprise: 规模化支持、设计系统、一致性
- SME/Startup: 效率、灵活性、成本可控
- 结合行业特点定制

**行动召唤 (2句)**
- 邀请查看: https://hueshadow.com
- 提供清晰下一步

**签名**
Rong Huang (黄蓉)
Senior UX Designer | Product Manager
Portfolio: https://hueshadow.com
LinkedIn: https://www.linkedin.com/in/ronn-huang-7b50273a3/
```

### 示例邮件

**项目**: DataViz Corp - Product Designer
**Match Score**: 80 (dashboard + Data Analytics + SME)

**TITLE**: Application: Product Designer – Data Visualization Expertise

```
Hi DataViz Team,

I noticed your Product Designer opening, and the focus on data visualization
dashboards caught my attention. During my 6 years at Huawei, I led the UX
for HUAWEI Analytics—a platform benchmarked against Google Analytics that
serves 21,000+ apps globally.

Translating complex data into intuitive interfaces is exactly what I do best.
I've designed everything from real-time monitoring dashboards to historical
trend analysis tools, balancing information richness with cognitive load.

I'd love to share my portfolio at https://hueshadow.com. Would you have
15 minutes this week for a quick conversation?

Best regards,
Rong Huang (黄蓉)
Senior UX Designer | Product Manager

Portfolio: https://hueshadow.com
Email: hueshadow989@gmail.com
```

---

## JSON 数据结构

```json
{
  "user_profile": {...},
  "high_match_count": 24,
  "total_valid_projects": 95,
  "projects": [
    {
      "id": 1,
      "is_valid": true,
      "validation_notes": null,
      "validated_at": "2026-01-10T10:00:00",
      "priority_score": 90,
      "match_score": 80,
      ...
    }
  ]
}
```

---

## 独立校验脚本

### 快速校验（仅格式检查）

```bash
python3 design-project-finder/verify_project_data.py
```

- 验证邮箱格式
- 验证链接格式
- 不检查可访问性（快速）

### 完整校验（含链接和活跃度）

```bash
python3 design-project-finder/verify_project_data.py --full-check --async
```

- 验证邮箱格式
- 验证链接格式
- 检查链接可访问性（Playwright MCP）
- 检查项目活跃度（Exa AI MCP）

### 输出

校验结果保存到 `design-project-finder/output/verified_projects.json`

```json
{
  "verified_at": "2026-01-10T10:00:00",
  "total_projects": 99,
  "valid_projects": 95,
  "invalid_projects": 4,
  "projects": [...]
}
```

---

## 文件结构

```
design-project-finder/
├── SKILL.md                        # 本文档
├── __init__.py                     # 包初始化 (v2.0)
├── user_profile.yaml               # 用户背景配置
│
├── # v2.0 核心模块
├── enhanced_email_validator.py     # 多层邮箱验证
├── smart_url_validator.py          # 智能URL验证
├── realtime_verifier.py            # 实时验证协调器
├── project_analyzer.py             # 项目需求深度分析
├── achievement_matcher.py          # 用户成就智能匹配
├── personalized_email_generator.py # 个性化邮件生成
├── disposable_domains.txt          # 一次性邮箱域名列表
│
├── # 辅助脚本
├── generate_marketing_emails.py    # 模板邮件生成
├── generate_ai_emails.py           # AI邮件生成脚本
└── verify_emails.py                # 邮件验证

output/
├── latest/                         # 指向最新日期
└── YYYY-MM-DD/
    ├── projects_for_ai_emails_*.json
    ├── design_projects_*.csv
    ├── contact_list_*.csv
    ├── design_projects_summary_*.md
    └── marketing_emails/
        ├── ai_generated/           # Claude 个性化邮件
        ├── high_priority/          # A/B级模板邮件
        └── medium_priority/        # C级模板邮件
```

---

## 用户配置 (user_profile.yaml)

```yaml
name: "黄蓉"
name_en: "Huang Rong"
email: "hueshadow989@gmail.com"
website: "https://hueshadow.com"
role_en: "Senior UX Designer / Product Manager"
years_experience: 10

expertise_keywords:
  high_match:
    - dashboard
    - analytics
    - data visualization
    - admin
    - b2b
    - saas
    - enterprise
  medium_match:
    - ui/ux
    - design system
    - mobile app
    - fintech

preferred_industries:
  high_priority:
    - SaaS
    - B2B
    - Data Analytics
    - FinTech
    - Enterprise Software
  medium_priority:
    - HealthTech
    - E-commerce
    - EdTech

preferred_client_types:
  high_priority:
    - Enterprise
    - SME

highlight_projects:
  - name: "HUAWEI Analytics"
    benchmark: "Google Analytics"
    result_en: "21,000+ apps integrated globally"
    keywords: [analytics, data, dashboard, tracking]

  - name: "Business Connect"
    benchmark: "Google My Business"
    result_en: "5.94 million merchants"
    keywords: [merchant, local, business, commerce]

  - name: "华为云费用中心"
    result_en: "Enterprise cloud billing system"
    keywords: [cloud, billing, enterprise, fintech]

email_signature: |
  Best regards,
  Rong Huang (黄蓉)
  Senior UX Designer | Product Manager
  Portfolio: https://hueshadow.com
  LinkedIn: https://www.linkedin.com/in/ronn-huang-7b50273a3/
```

---

## 执行检查清单

- [ ] 运行 `python3 process_design_projects.py` (自动校验)
- [ ] 检查 `Valid projects` 数量和过滤的项目
- [ ] 检查 `High match: X` 数量是否合理
- [ ] 查看 `output/latest/projects_for_ai_emails_*.json`
- [ ] 确认 `is_valid: true` 的项目数量
- [ ] 为 TOP 5 高匹配项目生成 AI 邮件
- [ ] 验证邮件: `python3 verify_emails.py`
- [ ] 人工审核后发送

### 校验相关问题排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| 邮箱格式错误 | 缺少 `@` 或域名 | 检查原始数据 |
| 链接缺少协议 | URL 未以 `http` 开头 | 手动补全或过滤 |
| 链接无法访问 | 网站已下线/404 | 移除或更新链接 |
| 项目已关闭 | 招聘已结束 | 使用 `--full-check --async` 验证 |

---

## 预期效果

| 指标 | 目标值 |
|------|--------|
| 总项目数 | 80-150 |
| 有效项目 | 75-145 (5-10% 过滤) |
| 高优先级 | 50-70 |
| 高匹配度 | 20-30 |
| 有邮箱联系 | 60-70% |
| 邮件响应率 | 15-20% |

---

## 版本历史

- **v2.0** (2026-01-10): 增强验证 + 深度个性化邮件
  - **多层邮箱验证**: 格式 → MX记录 → 一次性邮箱检测 → SMTP
  - **智能URL验证**: LinkedIn专用格式验证 + 异步可达性检测 + 缓存
  - **实时验证**: 数据收集时即验证，不再事后处理
  - **项目需求分析**: 自动提取技术需求、推断痛点、检测项目阶段
  - **成就智能匹配**: 多维度匹配用户作品集与项目需求
  - **推销角度优化**: 根据匹配结果确定最佳推销角度
  - 新增 `--realtime-verify`、`--generate-emails`、`--full` 参数

- **v1.1** (2026-01-09): 添加用户背景匹配、模板邮件生成
- **v1.0** (2026-01-08): 初始版本
