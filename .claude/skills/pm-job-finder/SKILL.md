---
name: pm-job-finder
description: "搜索海外PM职位平台(LinkedIn Jobs、AngelList、Remote OK等),找到适合的产品经理职位,分析匹配度,生成申请材料建议和公司研究报告。"
---

# PM职位搜索器 (PM Job Finder)

当用户想要寻找产品经理职位机会时，使用此技能。

## 激活条件
- 用户想要从 LinkedIn Jobs、AngelList、YC Jobs 等平台找PM职位
- 用户需要分析职位与自己背景的匹配度
- 用户想要获取公司研究报告或申请材料建议
- 用户提到"PM职位"、"产品经理工作"、"找PM工作"、"求职"

## 工作流程

### 步骤1: 需求确认
询问用户以下信息(如果未提供):
1. 目标职位级别 (Senior/Lead/Director/不限)
2. 目标平台 (默认: LinkedIn, AngelList, Remote OK, FlexJobs, YC Jobs)
3. 薪资期望范围 (最低/期望)
4. 公司阶段偏好 (早期创业/成长期/大厂/不限)
5. 行业偏好 (ToB SaaS/ToC Consumer/AI/不限)
6. 远程偏好 (全远程/混合/不限)
7. 地区偏好 (全球远程/中国大陆/亚太/北美/不限)

### 步骤2: 数据收集
使用 `mcp__exa__deep_researcher_start` 并行启动多个研究任务:

**第一批** (主流招聘平台):
- LinkedIn Jobs (Product Manager)
- Indeed (Product Manager)
- Glassdoor (Product Manager)

**第二批** (远程工作平台):
- Remote OK
- We Work Remotely
- FlexJobs
- Remotive

**第三批** (创业公司平台):
- AngelList/Wellfound
- YC Jobs (Y Combinator)
- BuiltIn

**第四批** (中国市场 - 可选):
- 拉勾网 (lagou.com)
- BOSS直聘

### 步骤3: 深度研究 Prompt 模板

```python
instructions = f"""
搜索 {platform} 上的产品经理(Product Manager)职位。

目标职位级别: {level}
目标地区: {regions}

对于每个职位,请提取:

**必需字段**:
1. 职位名称 (job_title)
2. 公司名称 (company_name)
3. 职位描述 (job_description) - 100-200字
4. 职责要求 (responsibilities) - 列表
5. 任职要求 (requirements) - 列表
6. 技能要求 (skills_required) - 列表
7. 职位级别 (job_level): Entry/Mid/Senior/Lead/Director/VP
8. 工作类型 (job_type): Full-time/Contract/Freelance
9. 远程政策 (remote_policy): Full Remote/Hybrid/On-site

**薪资信息**:
10. 薪资范围 (salary_range)
11. 薪资下限USD (salary_min_usd)
12. 薪资上限USD (salary_max_usd)
13. 是否有股权 (equity_offered): True/False

**公司信息** (核心字段):
14. 公司阶段 (company_stage): Seed/Series A/B/C/Growth/Public
15. 融资轮次 (funding_round)
16. 融资金额 (funding_amount)
17. 公司规模 (company_size)
18. 所属行业 (company_industry)
19. 产品类型 (product_type): ToB SaaS/ToC Consumer/ToB+ToC

**工作条件**:
20. 工作地点 (location)
21. 时区要求 (timezone_requirements)
22. 签证支持 (visa_sponsorship): True/False

**申请信息**:
23. 申请链接 (application_url)
24. 发布日期 (posted_date)

**联系信息** (尽可能提取):
25. 招聘者邮箱 (recruiter_email)
26. 招聘者LinkedIn (recruiter_linkedin)

**优先级判断**:
- 高: Senior/Lead级别 + 全远程 + 早期创业公司 + 薪资>$150K
- 中: Senior级别 或 混合办公
- 低: 初级职位 或 仅限现场

请至少找到 15-20 个活跃职位,重点关注有详细公司信息和薪资数据的。
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
运行 Python 脚本 `process_pm_jobs.py`:

**核心功能**:
1. **匹配评分**: 基于用户画像计算0-100分的匹配度
2. **数据清洗**: 薪资标准化、公司阶段分类、远程政策识别
3. **申请建议生成**: 简历重点、Cover Letter要点、面试准备

```python
def calculate_match_score(job, user_profile) -> int:
    """0-100分匹配度评分"""
    score = 0

    # 经验匹配 (25分)
    # 行业匹配 (20分)
    # 远程匹配 (20分)
    # 公司阶段匹配 (15分)
    # 薪资竞争力 (10分)
    # 技能匹配 (10分)

    return min(score, 100)

def determine_match_label(score: int) -> str:
    if score >= 80: return "A级-极高匹配"
    elif score >= 60: return "B级-高匹配"
    elif score >= 40: return "C级-中匹配"
    else: return "D级-低匹配"
```

### 步骤6: 生成输出
创建按日期组织的文件夹结构:

```
output/
├── latest/ → 指向最新日期文件夹的软链接
├── YYYY-MM-DD/
│   ├── pm_jobs_YYYY-MM-DD.csv           # 完整职位列表
│   ├── pm_jobs_summary_YYYY-MM-DD.md    # 匹配分析报告
│   ├── README.md                         # 使用说明
│   ├── match_analysis/                   # 按职位的匹配分析
│   │   ├── high_match/                   # A级匹配 (≥80分)
│   │   └── good_match/                   # B级匹配 (≥60分)
│   ├── application_materials/            # 申请材料建议
│   │   └── cover_letters/
│   └── company_research/                 # 公司调研报告
```

### 步骤7: 运行验证
```bash
python3 process_pm_jobs.py
```

检查输出:
- CSV文件包含所有预期列
- 匹配分数计算正确
- Summary报告生成完整
- Match analysis文件为高匹配职位生成

## 数据结构

```python
{
    # 职位信息
    "job_title": "Senior Product Manager - AI Platform",
    "company_name": "ByteDance",
    "job_description": "Lead product strategy for AI...",
    "responsibilities": ["Define product roadmap", "Work with ML team"],
    "requirements": ["5+ years PM experience", "AI/ML experience"],
    "skills_required": ["Product Strategy", "AI/ML", "Data Analysis"],
    "job_level": "Senior",
    "job_type": "Full-time",
    "remote_policy": "Full Remote",

    # 薪资
    "salary_range": "$180,000 - $250,000/year",
    "salary_min_usd": 180000,
    "salary_max_usd": 250000,
    "equity_offered": True,

    # 公司信息
    "company_stage": "Growth",
    "funding_round": "Series E",
    "funding_amount": "$3B",
    "company_size": "10000+",
    "company_industry": "Internet/AI",
    "product_type": "ToC Consumer",

    # 工作条件
    "location": "Remote (Global)",
    "timezone_requirements": "Flexible",
    "visa_sponsorship": True,

    # 申请信息
    "application_url": "https://...",
    "posted_date": "2026-01-05",
    "recruiter_email": "recruiter@company.com",
    "recruiter_linkedin": "https://linkedin.com/in/...",

    # 匹配分析 (计算生成)
    "match_score": 85,
    "match_label": "A级-极高匹配",
    "match_breakdown": {
        "experience_match": 25,
        "industry_match": 20,
        "remote_match": 20,
        "company_stage_match": 15,
        "salary_match": 10,
        "skills_match": 10
    },
    "match_highlights": ["8年经验匹配Senior级别", "全远程匹配偏好"],
    "match_concerns": [],

    # 申请支持 (生成)
    "resume_suggestions": ["突出AI产品经验", "量化用户增长数据"],
    "cover_letter_points": ["表达对AI产品的热情", "分享相关案例"],
    "interview_prep": ["准备AI产品案例", "研究公司产品线"]
}
```

## 输出规范

### CSV 文件
- **编码**: UTF-8-sig (Excel兼容)
- **排序**: 按匹配分数降序
- **列数**: 30+

**主要列**:
- 匹配等级、匹配分数、数据来源
- 职位名称、公司名称、职位级别、工作类型、远程政策
- 薪资范围、薪资下限USD、薪资上限USD
- 公司阶段、融资轮次、融资金额、公司规模
- 行业、产品类型
- 工作地点、时区要求、签证支持
- 申请链接、发布日期、发布天数
- 招聘者邮箱、招聘者LinkedIn
- 匹配亮点、匹配顾虑
- 简历重点建议、面试准备要点

### 匹配分析报告
包含:
- 数据概览 (总数、各级别分布、平均分)
- TOP 10 最佳匹配职位 (详细信息)
- 按平台统计 (各平台职位数、平均匹配分)
- 按行业/公司阶段分布
- 每周行动计划

### 申请材料建议
为A级和B级匹配职位生成:
- 简历重点建议 (基于职位要求)
- Cover Letter要点 (基于公司和职位特点)
- 面试准备提示 (基于公司和行业)

## 性能指标
- **执行时间**: 15-25分钟 (含深度研究)
- **覆盖平台**: 10+个
- **职位数量**: 50-100个
- **匹配分析生成**: A/B级职位自动生成详细分析

## 用户画像配置

用户可以在 `user_profile.py` 中配置个人偏好:

```python
USER_PROFILE = {
    "years_experience": 8,
    "target_level": ["Senior", "Lead", "Director"],
    "preferred_industries": {
        "ToB SaaS": 1.0,
        "AI/ML": 1.0,
        "ToC Consumer": 0.9,
    },
    "preferred_company_stages": {
        "Seed": 1.0,
        "Series A": 1.0,
        "Series B": 0.9,
    },
    "location_preferences": {
        "Full Remote": 1.0,
        "Hybrid": 0.6,
        "On-site": 0.2
    },
    "salary_expectation_min": 150000,
    "salary_expectation_target": 200000,
}
```

## 常见问题

### Q: 如何更新我的求职偏好？
A: 编辑 `user_profile.py` 文件中的 `USER_PROFILE` 字典，调整行业权重、公司阶段偏好、薪资期望等。

### Q: 为什么某些职位匹配分数低？
A: 匹配分数基于6个维度计算。查看职位的 `match_concerns` 字段了解具体原因。

### Q: 如何跟踪申请进度？
A: CSV输出可导入Notion/Airtable等工具跟踪。建议添加申请日期、面试状态等列。

### Q: 薪资数据不准确怎么办？
A: 部分平台不显示薪资。系统会使用行业中位数估算，建议在申请时确认实际薪资范围。

## 注意事项
1. 职位数据为快照，状态可能已变化
2. 建议每周运行一次获取最新职位
3. A级匹配优先申请，不要错过时机
4. 申请材料建议仅供参考，需根据个人经历调整
5. 面试前务必深入研究目标公司
6. 查看公司需求深度分析报告，了解各公司人才画像和行业趋势

## 版本
v1.1 - 2026-01-11
- 新增: 步骤8 公司需求深度挖掘
- 新增: 5大研究方向分析
- 新增: 技能差距分析
- 新增: 公司人才画像生成

v1.0 - 2026-01-09
- 初始版本

---

## 步骤8: 公司需求深度挖掘 (NEW - v1.1)

在完成职位匹配分析后，自动进行公司维度的需求深度分析:

```python
from company_analyzer import run_company_analysis

analysis_result, report_path = run_company_analysis(
    jobs=jobs,
    output_dir=DATE_DIR,
    use_llm=False
)
```

### 分析维度

1. **按公司聚合** - 将职位按公司分组，识别多职位公司的整体需求
2. **需求模式提取** - 提取各公司的技能要求、经验偏好、软技能需求
3. **人才画像生成** - 为每个公司生成理想候选人画像
4. **跨公司比较** - 识别共性需求和差异化因素
5. **5大研究方向** - 生成可执行的洞察和行动建议
6. **技能差距分析** - 对比用户技能与市场需求

### 5大研究方向

| # | 方向 | 描述 | 优先级 |
|---|------|------|--------|
| 1 | 最需求的技术技能 | 识别市场上PM最需要的技术能力 | 高 |
| 2 | 最受重视的项目经验 | 分析什么类型的项目经验最受青睐 | 高 |
| 3 | 领导力与软技能模式 | 提取对领导力和沟通的具体要求 | 中 |
| 4 | 行业特定要求 | 不同行业的特殊需求 | 中 |
| 5 | 新兴趋势 | AI、数据等新兴领域的需求趋势 | 高 |

### 输出文件

`company_research/company_requirements_analysis_YYYY-MM-DD.md`

### 报告结构

```
1. Executive Summary
   - 分析概览 (公司数、职位数、关键指标)
   - 核心发现摘要
   
2. Company-by-Company Analysis
   - 每个公司的人才需求画像
   - 必备技能 vs 加分项
   - 经验要求和领导力需求
   
3. Cross-Company Patterns
   - 通用要求 (80%+公司共有)
   - 技能需求频率排名
   - 公司聚类分析 (AI-First/Developer Tools/Growth等)
   
4. 5 Key Research Directions
   - 每个方向的详细分析
   - 关键发现和数据支持
   - 可执行洞察
   - 用户行动建议清单
   
5. Talent Profile Recommendations
   - 各Top公司理想候选人画像
   - 匹配策略建议
   - 面试准备重点
   
6. Skill Gap Analysis
   - 用户当前技能 vs 市场需求
   - 技能覆盖率
   - 优先提升的技能清单
   - 短中长期发展建议
```

### 技术实现

核心模块: `company_analyzer.py`

主要函数:
- `aggregate_by_company(jobs)` - 按公司聚合职位
- `extract_requirement_patterns(company_jobs)` - 提取需求模式
- `generate_company_profile(company, jobs, patterns)` - 生成公司人才画像
- `cross_company_analysis(groups, profiles)` - 跨公司分析
- `generate_research_directions(analysis, profiles, user_profile)` - 生成5大研究方向
- `analyze_skill_gaps(profiles, user_profile)` - 技能差距分析
- `generate_company_report(result, output_dir)` - 生成Markdown报告
