---
name: design-project-finder
description: "搜索海外设计工作平台(Fiverr、Upwork、Dribbble等),找到正在招聘设计师的项目,提取客户联系方式,生成个性化营销邮件推广 designsub.studio 设计订阅服务。"
---

# 设计项目与客户搜索器 (Design Project Finder)

当用户想要寻找海外设计项目机会、获取潜在客户联系方式、或推广设计订阅服务时，使用此技能。

## 激活条件
- 用户想要从 Fiverr、Upwork、Dribbble 等平台找设计项目
- 用户需要获取正在寻找设计师的客户联系方式
- 用户想要生成营销邮件推广设计服务
- 用户提到"设计客户"、"海外项目"、"设计订阅营销"

## 工作流程

### 步骤1: 需求确认
询问用户以下信息(如果未提供):
1. 目标设计类型 (UI/UX、品牌设计、网页设计、移动应用等)
2. 目标平台 (默认: Fiverr、Upwork、Dribbble、99designs、Behance、Toptal、LinkedIn)
3. 项目预算范围 (小型$100-500 / 中型$500-2000 / 大型$2000+ / 不限)
4. 客户类型偏好 (初创公司/中小企业/大企业/不限)
5. 营销邮件语气 (专业正式/友好亲切/创意活泼/自适应)

### 步骤2: 数据收集
使用 `mcp__exa__deep_researcher_start` 并行启动多个研究任务:

**第一批** (主流自由职业平台):
- Fiverr
- Upwork
- Freelancer
- Guru

**第二批** (设计专业平台):
- Dribbble Jobs
- Behance Jobs
- 99designs
- Designhill

**第三批** (扩展渠道):
- Toptal
- LinkedIn Jobs (Design)
- AngelList (Design roles)
- We Work Remotely (Design)

### 步骤3: 深度研究 Prompt 模板

```python
instructions = f"""
搜索 {{平台名称}} 上正在寻找{{设计类型}}设计师的活跃项目和客户。

目标设计类型: {{设计类型列表}}
预算范围: {{预算范围}}

对于每个项目,请提取:

**必需字段**:
1. 项目标题/需求描述
2. 客户名称/公司名称
3. 项目预算范围 (美元)
4. 项目详细要求 (100-200字)
5. 发布时间/更新时间
6. 项目状态 (开放中/招标中/紧急)

**工作范围 (核心字段 - 必须提取)**:
7. 需要做的工作 (What): 具体要设计什么? (如: 移动应用UI重新设计、品牌标识设计、网站前端设计等)
8. 交付物 (Deliverables): 需要交付什么成果? (如: Figma高保真原型、Logo源文件、设计系统文档等)
9. 交付格式 (Format): 需要以什么格式交付? (如: Figma、Sketch、PDF、HTML/CSS、可交互原型等)
10. 交付时间 (Timeline): 项目时间要求? (如: 4周内、紧急、2周内等)

**联系信息** (尽可能提取):
11. 客户邮箱地址
12. 客户LinkedIn链接
13. 公司网站
14. 平台项目链接

**客户背景**:
15. 客户行业/领域
16. 客户类型 (初创/中小企业/大企业/个人)
17. 以往发布项目数量
18. 客户评价/信誉分数

**优先级**:
- 高: 预算>$1000 且有联系方式 且工作范围明确
- 中: 预算>$500 或有部分联系方式
- 低: 其他

CRITICAL: 务必详细提取"工作范围"信息 - 这是评估项目价值和定制营销邮件的关键!
如果原始描述中没有明确说明工作范围、交付物、格式或时间，请基于项目标题和描述合理推断，并标注"[推断]"。

请至少找到 15-20 个活跃项目,重点关注有客户联系方式且工作范围明确的。
"""

model = "exa-research-pro"
```

### 步骤4: 轮询结果
使用 `mcp__exa__deep_researcher_check` 轮询所有任务直到完成:

```python
# 持续检查直到status为"completed"
while status == "running":
    result = mcp__exa__deep_researcher_check(taskId=task_id)
    # 等待5秒后再次检查
```

### 步骤5: 数据处理
创建 Python 脚本 `process_design_projects.py`:

**核心功能**:
1. **去重逻辑**: 基于标准化的 客户名+项目标题关键词+平台
2. **优先级评分**: 预算(40%) + 联系方式(30%) + 紧急度(15%) + 客户质量(15%)
3. **数据清洗**: 预算标准化、时间标准化、邮箱验证
4. **标签提取**: 行业标签、设计类型标签

```python
def calculate_priority_score(project: Dict) -> int:
    """0-100分优先级评分"""
    score = 0

    # 预算 (40分)
    budget = extract_budget_number(project['项目预算范围'])
    score += min(budget / 50, 40)  # $2000+ = 40分

    # 联系方式 (30分)
    if project.get('客户邮箱地址'): score += 15
    if project.get('客户LinkedIn链接'): score += 10
    if project.get('公司网站'): score += 5

    # 紧急度 (15分)
    if '紧急' in project.get('项目状态', '') or 'urgent' in project.get('项目状态', '').lower():
        score += 15
    elif '立即' in project.get('项目状态', '') or 'immediate' in project.get('项目状态', '').lower():
        score += 10

    # 客户质量 (15分)
    client_type = project.get('客户类型', '')
    if '大企业' in client_type or 'enterprise' in client_type.lower():
        score += 15
    elif '中小企业' in client_type or '初创' in client_type or 'startup' in client_type.lower():
        score += 10

    return min(score, 100)

def determine_priority_label(score: int) -> str:
    if score >= 70: return "A级-极高优先"
    elif score >= 50: return "B级-高优先"
    elif score >= 30: return "C级-中优先"
    else: return "D级-低优先"
```

### 步骤6: 营销邮件生成
创建 `generate_marketing_emails.py`:

**邮件生成策略**:
- 仅为 A级和 B级项目生成个性化邮件
- 基于客户需求和类型选择语气
- 自然融入 designsub.studio 价值主张

**邮件要素**:
1. **开场** (2-3句): 提到具体项目,展示理解
2. **价值主张** (3-4句): 针对需求说明订阅服务优势
3. **行动召唤** (2句): 邀请对话,提供下一步

**语气适配**:
- 初创公司 → 友好亲切,强调成本可控
- 中小企业 → 专业正式,强调效率和质量
- 大型企业 → 专业正式,强调规模化支持
- 个人创业者 → 创意活泼,强调灵活性

**邮件生成 Prompt 模板**:

```python
def generate_email_prompt(project: Dict, tone: str) -> str:
    return f"""
你是 designsub.studio 的设计顾问，为潜在客户撰写个性化营销邮件。

**客户项目信息**:
- 项目需求: {{project['项目标题']}}
- 详细要求: {{project['项目详细要求']}}
- 预算范围: {{project['项目预算范围']}}
- 客户类型: {{project['客户类型']}}
- 行业: {{project['客户所在行业']}}
- 平台: {{project['数据来源']}}

**designsub.studio 服务介绍**:
我们是一个设计订阅服务,提供:
- 无限次设计请求和修改
- 平均 48 小时内交付初稿
- 固定月费,无隐藏费用
- 专业 UI/UX、品牌、网页设计团队
- 可随时暂停或取消订阅
- 适合需要持续设计支持的团队

**你的任务**:
撰写一封 {{tone}} 语气的营销邮件（150-200词）

**邮件结构**:
1. **开场** (2-3句):
   - 提到你在 {{project['数据来源']}} 看到他们的项目
   - 展示你对他们具体需求的理解
   - 引起兴趣,不要直接推销

2. **价值主张** (3-4句):
   - 针对他们的具体需求,说明设计订阅服务的优势
   - 例如: 如果是初创公司→强调成本可控性和灵活性
   - 例如: 如果预算紧张→强调性价比和无限修改
   - 例如: 如果需求多样→强调无限次请求和快速交付

3. **行动召唤** (2句):
   - 邀请简短对话/查看案例
   - 提供清晰的下一步

**要求**:
- 长度: 150-200 词
- 语气: {{tone}}
- 避免: 模板化语言、过度推销、空洞承诺
- 体现: 专业性、对项目的真正理解、真诚
- 自然融入 designsub.studio 而不是生硬插入
- 使用英文撰写（因为是海外客户）

请直接输出邮件正文,不要包含主题行或签名。
"""
```

### 步骤7: 生成输出
创建按日期组织的文件夹结构:

```
output/
├── latest/ → 指向最新日期文件夹的软链接
├── YYYY-MM-DD/ (如 2026-01-08)
│   ├── design_projects_YYYY-MM-DD.csv  - 完整项目数据
│   ├── contact_list_YYYY-MM-DD.csv     - 纯联系方式列表
│   ├── design_projects_summary_YYYY-MM-DD.md - 统计分析报告
│   ├── README.md                       - 使用说明
│   └── marketing_emails/               - 个性化邮件文件夹
│       ├── high_priority/              - A/B级项目邮件
│       └── medium_priority/            - C级项目邮件
└── archive/                            - 归档旧数据（手动管理）
```

**说明**:
- 每次运行创建新的日期文件夹
- `output/latest` 自动更新指向最新日期文件夹
- 保留历史数据，便于对比不同日期的收集结果
- 支持每日运行，长期积累项目数据库

### 步骤7.5: 邮件内容验证 ⭐ **关键步骤**
在生成输出后，**必须验证**所有营销邮件中的占位符已被正确替换:

**验证方法**:
```bash
# 检查是否有未替换的占位符
grep -r "{industry}" output/marketing_emails/
grep -r "{title}" output/marketing_emails/
grep -r "{client}" output/marketing_emails/

# 如果输出为空，说明没有占位符残留 ✅
```

**常见问题及修复**:

| 问题 | 原因 | 修复方法 |
|------|------|----------|
| `{industry}` 未替换 | f-string 缺少 `f` 前缀 | `value_prop = f"..."` |
| `{title}` 未替换 | 多行字符串中变量未用 f-string | 将整段改为 f-string |
| `None` 出现在邮件中 | 可选字段为空 | 使用 `or ''` 提供默认值 |

**自动验证脚本**:
```python
import re
import os

def verify_emails(email_dir="output/marketing_emails"):
    """验证所有邮件文件没有未替换的占位符"""
    placeholder_pattern = r'\{[a-zA-Z_]+\}'
    issues = []

    for root, dirs, files in os.walk(email_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(placeholder_pattern, content)
                    if matches:
                        issues.append({
                            'file': filepath,
                            'placeholders': list(set(matches))
                        })

    if issues:
        print("❌ 发现未替换的占位符:")
        for issue in issues:
            print(f"  - {issue['file']}: {issue['placeholders']}")
        return False
    else:
        print("✅ 所有邮件已正确生成，无占位符残留")
        return True

# 运行验证
if __name__ == "__main__":
    verify_emails()
```

**修复后的 f-string 正确写法**:
```python
# ❌ 错误: 普通字符串中的变量不会被替换
value_prop = "We've helped several {industry} startups..."

# ✅ 正确: f-string 会正确替换变量
value_prop = f"We've helped several {industry} startups..."
```

**验证流程**:
1. 运行 `python3 process_design_projects.py`
2. 执行验证脚本: `python3 verify_emails.py`
3. 如果发现问题，检查 `generate_email_content()` 函数中的 f-string
4. 重新生成邮件
5. 再次验证直到通过

**未经验证的邮件不得用于营销推广！**

### 步骤8: 版本控制 (可选)
```bash
git add output/
git commit -m "Add design project collection from 12 platforms with marketing emails"
git push -u origin design-projects-{date}
gh pr create --title "Design Project Collection - {date}" --body "..."
```

## 数据结构

```python
{
    # 优先级
    "优先级标签": "A级-极高优先",
    "优先级分数": 85,
    "数据来源": "Upwork",

    # 项目信息
    "项目标题": "SaaS Dashboard Redesign",
    "项目详细要求": "...",
    "设计类型标签": "UI/UX",
    "项目状态": "紧急",

    # 工作范围 (新增 - 核心字段)
    "需要做的工作": "重新设计SaaS仪表板界面，包括用户流程优化、高保真原型和可交互演示",
    "交付物": "Figma设计文件、交互原型( InVision)、设计系统文档、源文件",
    "交付格式": "Figma、InVision可交互原型、PDF文档",
    "交付时间": "4周内完成初稿，2轮迭代",

    # 预算
    "项目预算范围": "$2,000 - $3,500",
    "预算下限USD": 2000,
    "预算上限USD": 3500,
    "预算中值USD": 2750,

    # 客户
    "客户名称": "TechStartup Inc",
    "客户类型": "初创公司",
    "客户所在行业": "SaaS/B2B",
    "客户信誉分数": "4.8/5",
    "客户以往项目数": 15,

    # 联系方式
    "客户邮箱地址": "john@techstartup.com",
    "邮箱有效性": "已验证",
    "客户LinkedIn链接": "linkedin.com/in/john",
    "公司网站": "techstartup.com",
    "平台项目链接": "upwork.com/jobs/...",

    # 时间
    "发布时间": "2 days ago",
    "发布时间标准化": "2026-01-06",
    "距今天数": 2,

    # 营销
    "是否已生成邮件": "是",
    "邮件文件路径": "marketing_emails/high_priority/project_001_TechStartup.md",
    "推荐联系方式": "邮箱优先",

    # 元数据
    "数据收集时间": "2026-01-08 14:30"
}
```

## 输出规范

### CSV 文件
- **编码**: UTF-8-sig (Excel兼容)
- **排序**: 按优先级分数降序
- **列数**: 25+

**主要列**:
- 优先级标签、优先级分数、数据来源
- 项目标题、详细要求、设计类型标签、项目状态
- **需要做的工作、交付物、交付格式、交付时间** (新增)
- 预算范围、预算下限/上限/中值（USD）
- 客户名称、类型、行业、信誉分数
- 邮箱地址、邮箱有效性、LinkedIn链接、公司网站、项目链接
- 发布时间、标准化时间、距今天数
- 是否已生成邮件、邮件文件路径、推荐联系方式

### 统计报告
包含:
- 数据概览 (总数、去重后、有效联系率、已生成邮件数)
- 按优先级统计 (项目数、平均预算、有联系方式比例)
- 按数据来源统计 (各平台项目数、平均预算、有效率)
- 按客户类型统计
- 按设计类型统计
- 按预算分布统计
- TOP 10 重点推荐项目 (详细信息 + 联系方式)
- 营销活动建议 (行动计划、推荐策略、预期转化率)
- 下一步行动清单

### 营销邮件
- **格式**: Markdown
- **长度**: 150-200词
- **语言**: 英文（针对海外客户）
- **包含**:
  - Subject lines (3个备选)
  - Email body
  - 项目基本信息摘要
- **存储**: 按优先级分文件夹

**邮件文件命名**: `project_{编号}_{客户名称}_email.md`

## 性能指标
- **执行时间**: 20-30分钟
- **覆盖平台**: 12+个
- **项目数量**: 80-150个
- **有效联系率**: 60-70%
- **自动生成邮件**: 40-60封（A/B级项目）

## 常见问题

### Q: 如何提高联系方式提取率?
A: (1) 使用 exa-research-pro 模型 (2) 在 prompt 中明确要求提取邮箱和LinkedIn (3) 搜索公司官网的联系页面 (4) 根据公司域名构造常见邮箱格式

### Q: 邮件如何避免被标记为垃圾邮件?
A: (1) 个性化每封邮件 (2) 不使用模板化语言 (3) 提到具体项目需求 (4) 使用正规商业邮箱发送 (5) 小批量发送,避免群发 (6) 包含真实的联系信息和公司网站

### Q: 如何判断邮件语气?
A: 脚本会根据客户类型自动选择: 初创公司→友好亲切, 大企业→专业正式, 个人→创意活泼。也可在步骤1中手动指定语气偏好。

### Q: 预算范围不统一怎么办?
A: `extract_budget()` 函数会处理各种格式: "$1000-2000", "1k-2k", "Fixed: $1500", "Up to $3000" 等,统一转换为数值。

### Q: 如何跟踪营销效果?
A: CSV 包含"联系状态"、"回复时间"等字段,可导入 CRM 或使用 Airtable/Notion 跟踪。建议两周后重新运行技能获取新项目。

### Q: 某些平台搜索失败怎么办?
A: Exa AI 已处理大部分反爬虫机制。如果仍然失败: (1) 调整 prompt 更具体描述平台 (2) 减少该平台的请求数量 (3) 使用备用平台 (4) 手动补充该平台数据

### Q: 如何定制邮件模板?
A: 编辑 `templates/email_templates.md` 文件,添加自己的模板和话术。也可以修改 `generate_email_prompt()` 函数来调整邮件生成逻辑。

## 注意事项
1. 遵守各平台使用条款,仅用于合法商业开发
2. 验证邮箱有效性后再发送,避免高退信率
3. 个性化邮件需人工审核后再发送（特别是前5-10封）
4. 数据为快照,项目状态可能已变化
5. 部分平台需要登录才能看到完整联系方式
6. 尊重客户隐私,不要滥用联系信息
7. 如果收到不感兴趣的回复,立即停止联系

## 成功案例参考

**预期工作流程**:
1. 运行技能收集 100+ 个设计项目
2. 筛选出 40-50 个 A/B级高优先项目
3. 人工审核自动生成的邮件,微调 5-10 封
4. 小批量发送（每天 10-15 封）
5. 跟踪响应率和转化率
6. 两周后重新运行收集新项目

**预期转化率**:
- 邮件打开率: 25-35%
- 响应率: 8-12%
- 潜在客户对话: 4-6 个
- 新订阅客户: 1-2 个/轮

## 版本
v1.0 - 2026-01-08
