# PM Job Finder

智能PM职位搜索和匹配分析工具，帮助产品经理高效找到适合的工作机会。

## 功能特点

- **多平台搜索**: 覆盖 LinkedIn Jobs、AngelList、Remote OK、YC Jobs 等 10+ 平台
- **智能匹配评分**: 基于经验、行业、远程政策、公司阶段、薪资等 6 个维度计算匹配度
- **申请材料建议**: 针对每个职位生成简历重点、Cover Letter要点、面试准备提示
- **公司调研报告**: 自动收集公司背景、融资历史、产品信息

## 快速开始

### 1. 配置用户画像

编辑 `user_profile.py` 设置你的求职偏好:

```python
USER_PROFILE = {
    "years_experience": 8,              # 工作年限
    "target_level": ["Senior", "Lead"], # 目标级别
    "preferred_industries": {            # 行业偏好 (权重0-1)
        "ToB SaaS": 1.0,
        "AI/ML": 1.0,
    },
    "location_preferences": {            # 远程偏好
        "Full Remote": 1.0,
        "Hybrid": 0.6,
    },
    "salary_expectation_min": 150000,   # 最低薪资期望
    "salary_expectation_target": 200000, # 目标薪资
}
```

### 2. 运行处理脚本

```bash
python3 process_pm_jobs.py
```

### 3. 查看输出

```
output/latest/
├── pm_jobs_2026-01-09.csv           # 完整职位列表
├── pm_jobs_summary_2026-01-09.md    # 匹配分析摘要
├── match_analysis/                   # 高匹配职位详细分析
│   ├── high_match/                   # A级 (≥80分)
│   └── good_match/                   # B级 (≥60分)
└── README.md                         # 使用说明
```

## 匹配评分算法

| 维度 | 权重 | 说明 |
|------|------|------|
| 经验匹配 | 25分 | 职位级别 vs 你的工作年限 |
| 行业匹配 | 20分 | 公司行业 vs 你的偏好 |
| 远程匹配 | 20分 | 远程政策 vs 你的偏好 |
| 公司阶段 | 15分 | 早期创业/大厂 vs 你的偏好 |
| 薪资竞争力 | 10分 | 薪资范围 vs 你的期望 |
| 技能匹配 | 10分 | 要求技能 vs 你的技能 |

**匹配等级**:
- **A级 (≥80分)**: 极高匹配 - 立即申请
- **B级 (60-79分)**: 高匹配 - 强烈推荐
- **C级 (40-59分)**: 中匹配 - 可考虑
- **D级 (<40分)**: 低匹配 - 不太适合

## 目录结构

```
PM-job-finder/
├── process_pm_jobs.py      # 主处理脚本
├── user_profile.py         # 用户配置文件
├── pm-job-finder/          # Claude Code Skill
│   ├── SKILL.md            # 技能定义
│   └── README.md           # 本文件
└── output/                 # 输出目录
    ├── latest/             # 软链接到最新输出
    └── YYYY-MM-DD/         # 按日期组织的输出
```

## 使用建议

1. **每周运行一次** - 保持职位数据新鲜
2. **优先申请A级** - 匹配度高的职位不要错过
3. **定制Cover Letter** - 使用生成的要点，但要个性化
4. **跟踪申请进度** - 将CSV导入Notion/Airtable管理

## 支持的平台

| 平台 | 类型 | 特点 |
|------|------|------|
| LinkedIn Jobs | 综合招聘 | 大厂、全职为主 |
| AngelList/Wellfound | 创业公司 | 早期机会、股权 |
| Remote OK | 远程工作 | 全球远程职位 |
| We Work Remotely | 远程工作 | 高质量远程 |
| YC Jobs | 创业公司 | YC孵化公司 |
| Indeed | 综合招聘 | 覆盖广 |
| Glassdoor | 综合招聘 | 有公司评价 |
| BOSS直聘 | 中国市场 | 国内职位 |

## 版本历史

- **v1.0** (2026-01-09): 初始版本
  - 多平台职位搜索
  - 智能匹配评分
  - 申请材料建议生成

## License

MIT
