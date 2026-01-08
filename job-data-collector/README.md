# Job Data Collector Skill

## 技能描述
自动从多个招聘渠道收集职位信息，进行数据清洗、去重、分类，并生成结构化的CSV报告。

## 核心功能
1. 多渠道并行数据收集（Boss直聘、LinkedIn、猎聘、拉勾、51Job等11+渠道）
2. 智能去重与数据标准化
3. 优先级分类（远程/目标城市/其他）
4. 生成Excel兼容CSV + 统计分析报告

## 使用方法
激活技能后，告诉AI：
"帮我收集[职位名称]的职位信息，优先[远程/城市]，目标城市：[城市列表]"

示例：
"帮我收集AI产品经理的职位信息，优先远程，目标城市：北京、上海、杭州"

## 输出文件
- {job_type}_jobs_extended.csv - 完整职位数据
- {job_type}_jobs_summary.md - 统计分析报告
- README_EXTENDED.md - 详细使用说明
- process_jobs_extended.py - 数据处理脚本

## 技术特点
- 使用Exa AI Deep Research进行多渠道并行搜索
- Python自动化数据处理
- 智能去重算法
- 优先级自动排序
- Git版本控制集成
