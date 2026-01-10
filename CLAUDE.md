# Design Job Finder

这是一个帮助 UX 设计师搜索海外设计项目、验证信息真实性、并生成个性化营销邮件的工具。

## Skills

- [Design Project Finder](./design-project-finder/SKILL.md) - 搜索、验证和邮件生成工具 (v2.0)

## 快速开始

```bash
# 基础运行
python3 process_design_projects.py

# 带增强验证
python3 process_design_projects.py --realtime-verify

# 生成AI邮件
python3 process_design_projects.py --generate-emails

# 完整模式（验证+邮件）
python3 process_design_projects.py --full
```

## 项目结构

```
├── process_design_projects.py     # 主入口脚本
├── design-project-finder/         # Skill 模块
│   ├── SKILL.md                   # Skill 文档
│   ├── enhanced_email_validator.py
│   ├── smart_url_validator.py
│   ├── realtime_verifier.py
│   ├── project_analyzer.py
│   ├── achievement_matcher.py
│   └── personalized_email_generator.py
└── output/                        # 输出目录
    └── latest/                    # 最新输出
```

## 依赖

```bash
pip install aiohttp dnspython cachetools pyyaml
```
