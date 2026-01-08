---
name: job-data-collector
description: "从多个招聘渠道（Boss直聘、LinkedIn、猎聘等）收集职位信息，去重整理并输出CSV表格。用于职位搜索、求职调研、职位数据聚合。"
---

# 职位数据收集器 (Job Data Collector)

当用户请求收集某个职位的招聘信息时，使用此技能。

## 激活条件
- 用户想要收集/查找某个职位的招聘信息
- 用户想要从多个渠道聚合职位数据
- 用户需要职位市场调研数据
- 用户想要整理求职信息

## 工作流程

### 步骤1: 需求确认
询问用户以下信息（如果未提供）：
1. 目标职位名称（如"AI产品经理"、"前端工程师"）
2. 地域偏好（远程优先 或 指定城市）
3. 目标城市列表（如果不是纯远程）
4. 其他要求（薪资范围、公司类型等）

### 步骤2: 制定计划
使用EnterPlanMode创建详细实施计划：
\`\`\`markdown
## 项目目标
从多个招聘渠道收集{职位名称}职位信息，输出CSV格式表格

## 数据来源
- 国内主流: Boss直聘、猎聘、拉勾、51Job、智联招聘
- 国际平台: LinkedIn
- 垂直社区: 脉脉、V2EX、电鸭社区
- 其他: 公司官网、即刻

## 实施方案
### 阶段1: 数据收集
- 分3批并行启动深度研究任务
- 第一批: 猎聘、拉勾、51Job、智联
- 第二批: 脉脉、V2EX、电鸭
- 第三批: 公司官网、即刻

### 阶段2: 数据处理
- 创建Python脚本进行数据清洗
- 实现去重逻辑（基于公司名+职位名）
- 计算优先级（远程 > 目标城市 > 其他）

### 阶段3: 输出生成
- 生成CSV文件（Excel兼容）
- 生成统计报告（Markdown）
- 生成README文档
\`\`\`

### 步骤3: 数据收集
使用\`mcp__exa__deep_researcher_start\`并行启动多个研究任务：

**第一批**（国内主流平台）:
\`\`\`python
mcp__exa__deep_researcher_start(
    instructions=f"""搜索猎聘网（liepin.com）上{职位名称}职位。
    目标城市：{远程/城市列表}
    对于每个职位，请提取：
    1. 公司名称
    2. 职位名称  
    3. 工作地点
    4. 办公模式（远程/线下/混合）
    5. 薪资范围
    6. 主要职位要求（≤100字）
    7. 职位链接
    请至少找到15-20个符合条件的职位。""",
    model="exa-research-pro"
)
\`\`\`

对拉勾、51Job、智联重复此过程。

**第二批**（垂直渠道）:
- 脉脉、V2EX、电鸭社区

**第三批**（其他渠道）:
- 公司官网、即刻、小红书

### 步骤4: 轮询结果
使用\`mcp__exa__deep_researcher_check\`轮询所有任务，直到完成：
\`\`\`python
# 持续检查直到status为"completed"
while status == "running":
    result = mcp__exa__deep_researcher_check(taskId=task_id)
\`\`\`

### 步骤5: 数据处理
创建Python脚本 \`process_jobs_extended.py\`:
\`\`\`python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from datetime import datetime
from typing import List, Dict

def normalize_company_name(name: str) -> str:
    """标准化公司名称"""
    # 移除常见后缀
    suffixes = ['有限公司', '股份有限公司', 'Ltd', 'Inc']
    for suffix in suffixes:
        name = name.replace(suffix, '')
    return name.strip().lower()

def is_duplicate(job: Dict, existing_jobs: List[Dict]) -> bool:
    """检查是否重复"""
    company = normalize_company_name(job['公司名称'])
    title = job['职位名称'].lower()
    
    for existing in existing_jobs:
        if (normalize_company_name(existing['公司名称']) == company 
            and existing['职位名称'].lower() == title):
            return True
    return False

def determine_priority(location: str, mode: str) -> str:
    """计算优先级"""
    if "远程" in mode or "Remote" in mode:
        return "高"
    if location in target_cities:
        return "中"
    return "低"

# 主处理逻辑
all_jobs = []
# 从研究报告中提取数据
# 去重
# 排序
# 导出CSV
\`\`\`

### 步骤6: 生成输出
创建以下文件：
1. \`output/{job_type}_jobs_extended.csv\` - 完整数据
2. \`output/{job_type}_jobs_summary.md\` - 统计报告
3. \`README_EXTENDED.md\` - 使用说明
4. \`.gitignore\` - Git配置

### 步骤7: 版本控制
\`\`\`bash
git add .
git commit -m "Add {job_type} job collection from 11 channels"
git push -u origin {branch-name}
gh pr create --base main --title "..." --body "..."
\`\`\`

## 核心代码模板

### 深度研究Prompt模板
\`\`\`
搜索{平台名称}上{职位名称}职位。

目标城市：{远程办公职位、城市A、城市B、城市C}

对于每个职位，请提取：
1. 公司名称
2. 职位名称
3. 工作地点（具体城市或标注"远程"）
4. 办公模式（远程/线下/混合）
5. 薪资范围（如"25K-40K"）
6. 主要职位要求（精简到100字以内）
7. 职位链接

重点关注：
- 优先收集远程职位
- 尽可能收集完整的薪资信息

请至少找到15-20个符合条件的职位。
\`\`\`

### 数据结构
\`\`\`python
{
    "优先级": "高/中/低",
    "数据来源": "Boss直聘/LinkedIn/...",
    "公司名称": "阿里巴巴",
    "职位名称": "AI产品经理",
    "工作地点": "远程",
    "办公模式": "远程/线下/混合",
    "薪资范围": "35K-60K",
    "职位要求": "需5年以上产品经验...",
    "职位链接": "https://...",
    "更新时间": "2026-01-02 17:06"
}
\`\`\`

## 输出规范

### CSV文件
- 编码: UTF-8-sig（Excel兼容）
- 分隔符: 逗号
- 排序: 按优先级（高>中>低）

### 统计报告结构
\`\`\`markdown
# {职位名称}职位统计报告

## 数据概览
- 总职位数: X 条
- 更新时间: YYYY-MM-DD HH:MM

## 按数据来源统计
- Boss直聘: X 条
- LinkedIn: X 条
...

## 按优先级统计
- 高优先级: X 条
- 中优先级: X 条
- 低优先级: X 条

## 按工作地点统计（TOP 10）
...

## 重点推荐
### 远程职位（TOP 10）
...

### 目标城市高薪职位（TOP 10）
...
\`\`\`

## 性能指标
- 执行时间: 15-25分钟
- 覆盖渠道: 10+个
- 职位数量: 50-150个
- 去重率: <10%

## 常见问题

### Q: 如何添加新的招聘渠道？
A: 在步骤3中添加新的\`deep_researcher_start\`任务，指定新渠道的URL和搜索策略。

### Q: 如何处理薪资格式不统一？
A: 在Python脚本中实现\`normalize_salary()\`函数，统一转换为"XXK-XXK"格式。

### Q: 去重规则是什么？
A: 基于标准化后的公司名+职位名，同时检查职位链接是否相同。

### Q: 如何自定义优先级规则？
A: 修改\`determine_priority()\`函数中的逻辑。

## 注意事项
1. 遵守各招聘平台的使用条款
2. 仅用于个人求职参考
3. 数据为快照，需注明收集时间
4. 部分职位链接可能为示例

## 成功案例
- AI产品经理: 11个渠道，61个职位，27分钟
- 预期其他职位类型有类似性能

## 版本
v1.0 - 2026-01-02
