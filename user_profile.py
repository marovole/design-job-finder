#!/usr/bin/env python3
"""
PM Job Finder - User Profile Configuration
Defines user preferences for job matching algorithm.

Profile: 陆先生 (@marovole)
Positioning: CCO (Chief Context Officer) + Vibe Coder
"""

# =============================================================================
# AI AGENT KEYWORDS - 用于检测职位的 AI 相关性
# =============================================================================
AI_AGENT_KEYWORDS = [
    # 直接匹配 - AI Agent 相关
    "ai agent", "llm", "large language model", "gpt", "claude",
    "ai assistant", "conversational ai", "ai workflow", "ai automation",
    "chatbot", "copilot", "ai-powered",
    # 通用 AI/ML
    "artificial intelligence", "machine learning", "deep learning",
    "genai", "generative ai", "foundation model", "ai platform",
    "ai infrastructure", "mlops",
    # AI 产品应用
    "ai product", "ai application", "ai saas", "prompt engineering",
    "ai tools", "ai coding", "ai developer",
    # 技术栈
    "openai", "anthropic", "huggingface", "langchain", "llamaindex",
]

# =============================================================================
# SKILL WEIGHTS - 技能匹配权重配置
# =============================================================================
SKILL_WEIGHTS = {
    "ai_agent_skills": 1.5,      # AI Agent 专项技能权重 x1.5
    "core_skills": 1.0,          # 核心 PM 技能标准权重
    "technical_skills": 0.8,     # 技术技能权重稍低
    "domain_expertise": 1.2      # 领域专业权重
}

# AI 相关职位的额外加分（最高 15 分）
AI_RELEVANCE_BONUS_MAX = 15

# =============================================================================
# USER PROFILE
# =============================================================================
USER_PROFILE = {
    # === Basic Info ===
    "years_experience": 10,
    "current_title": "Product Director / Head of Product",
    "target_level": ["Senior", "Lead", "Director", "Head of Product", "VP"],

    # === Personal Brand ===
    "personal_brand": {
        "twitter": "@marovole",
        "email": "marovole@gmail.com",
        "positioning": "CCO (Chief Context Officer) + Vibe Coder",
        "unique_value": "AI Agent expert who can design AND build production-ready AI workflows",
        "tagline": "能在高不确定场景中补齐上下文、对齐目标与边界，降低协作偏差并稳定产出高质量交付"
    },

    # === Industry Preferences (weights: 0.0 - 1.0) ===
    # AI 优先，Web3 次之
    "preferred_industries": {
        # AI 相关 - 最高优先级
        "AI/ML": 1.0,
        "AI Agent/LLM Apps": 1.0,
        "Developer Tools": 1.0,
        "AI Infrastructure": 0.95,

        # Web3 相关 - 有深度经验
        "Web3/Crypto": 0.95,
        "DeFi": 0.9,
        "GameFi": 0.85,
        "NFT/Digital Assets": 0.8,

        # 传统互联网
        "ToB SaaS": 0.9,
        "Data Products": 0.85,
        "ToC Consumer": 0.8,
        "Platform/Marketplace": 0.8,
        "Enterprise Software": 0.7,
        "FinTech": 0.7,
        "EdTech": 0.5,
        "HealthTech": 0.5,
        "E-commerce": 0.5,
        "Other": 0.3
    },

    # === Company Stage Preferences (weights: 0.0 - 1.0) ===
    "preferred_company_stages": {
        "Pre-seed": 0.8,
        "Seed": 1.0,              # Highest - early stage startup
        "Series A": 1.0,          # Highest - early stage startup
        "Series B": 0.9,
        "Series C": 0.7,
        "Series D+": 0.5,
        "Growth": 0.6,
        "Public": 0.4,
        "Enterprise": 0.3
    },

    # === Location & Remote Preferences ===
    "location_preferences": {
        "Full Remote": 1.0,       # Highest priority
        "Remote-first": 1.0,
        "Hybrid": 0.6,
        "On-site": 0.2
    },
    "preferred_regions": [
        "Global Remote",
        "China Mainland",
        "Asia Pacific",
        "US (Remote OK)",
        "Europe (Remote OK)"  # 德国创业经验
    ],

    # === Salary Expectations (USD) ===
    "salary_expectation_min": 120000,  # ~85K RMB/月
    "salary_expectation_target": 180000,  # ~130K RMB/月
    "currency": "USD",

    # === Job Type Preferences ===
    "preferred_job_types": {
        "Full-time": 1.0,
        "Contract": 0.8,
        "Freelance": 0.7,
        "Part-time": 0.4
    },

    # === AI Agent 专项技能（核心差异化）===
    "ai_agent_skills": [
        "AI Agent Architecture & Design",
        "Skills/Workflow Development (Claude Code, MCP)",
        "Vertical Agent Multi-scenario Applications",
        "Prompt Engineering & Optimization",
        "LLM Application Development",
        "AI Coding Tools (Cursor/Codex/Opencode)",
        "AI-assisted Rapid Prototyping",
        "AI Tool Team Adoption & Scaling",
        "AI Image Generation (SD/LoRA/Inpaint)"
    ],

    # === Core PM Skills ===
    "core_skills": [
        # AI/Agent 相关
        "AI Agent Product Design",
        "LLM Application Strategy",
        "AI Workflow Automation",
        "Prompt Engineering",

        # 传统 PM 技能
        "Product Strategy (0→1)",
        "Product Roadmap",
        "User Research",
        "Data-Driven Decision Making",
        "A/B Testing",
        "Agile/Scrum",
        "Stakeholder Management",
        "Cross-functional Leadership",
        "OKR & Goal Setting",
        "Go-to-Market Strategy",
        "Product Discovery",

        # Web3 特有
        "Tokenomics Design",
        "DeFi Product Design",
        "NFT/GameFi Mechanics"
    ],

    # === Technical Skills ===
    "technical_skills": [
        # AI 工具链
        "Claude Code",
        "Cursor",
        "Codex",
        "Opencode",
        "MCP (Model Context Protocol)",
        "Skills Development",
        "Stable Diffusion",
        "LoRA Fine-tuning",
        "ChatGPT/GPT-4",
        "Midjourney",

        # 数据分析
        "SQL",
        "Python",
        "Analytics (Amplitude/Mixpanel)",
        "Tableau/Looker",

        # 设计
        "Figma",
        "High-fidelity Prototyping",

        # 项目管理
        "Jira",
        "Notion",

        # Web3
        "Smart Contract Basics",
        "DeFi Protocols",
        "NFT Standards",
        "Wallet Integration"
    ],

    # === Domain Expertise ===
    "domain_expertise": [
        "AI Agent Applications",
        "LLM-powered Products",
        "AI Coding Tools",
        "Web3/DeFi/GameFi",
        "Tokenomics",
        "Cross-border Products",
        "Platform/Marketplace Products",
        "Mobile Apps (iOS/Android)",
        "Community Products",
        "Social + E-commerce"
    ],

    # === Work Experience Highlights ===
    "experience_highlights": [
        {
            "company": "Infinite Pixel Frontier Limited",
            "role": "Product Director",
            "duration": "2023.07-Present",
            "highlights": [
                "多条产品线 0→1 规划与交付（游戏、ToB SaaS、Telegram 小游戏、DEX、预测市场）",
                "推动 AI 工具在团队规模化应用",
                "在高不确定场景完成业务目标拆解与跨团队协同"
            ]
        },
        {
            "company": "LIDA",
            "role": "Product Manager",
            "duration": "2023.06-2023.08",
            "highlights": [
                "从 0→1 打造 AI 绘图移动端 APP",
                "基于 SD1.5 + LoRA + Inpaint 实现完整产品闭环",
                "完成 App Store / Google Play 上架"
            ]
        },
        {
            "company": "Citygram UG (Co-Founder)",
            "role": "Product Manager",
            "duration": "2016.09-2022.05",
            "highlights": [
                "德国华人社区 APP，持续运营6年",
                "输出 200+ 页面高保真设计",
                "管理 10-20 人跨时区团队",
                "App Store 保持 4.7 分以上评分"
            ]
        }
    ],

    # === Language Skills ===
    "languages": {
        "Chinese": "Native",
        "English": "Professional",
        "German": "DSH-1 (Basic Professional)"
    }
}


def get_user_profile():
    """Return the user profile configuration"""
    return USER_PROFILE


def get_experience_level_ranges():
    """
    Define experience requirements for each job level.
    Returns dict mapping level -> (min_years, max_years)
    """
    return {
        'Entry': (0, 2),
        'Junior': (1, 3),
        'Mid': (2, 5),
        'Senior': (5, 10),
        'Lead': (7, 12),
        'Principal': (8, 15),
        'Director': (10, 20),
        'Head of Product': (8, 20),
        'VP': (12, 25),
        'C-Level': (15, 30)
    }


def get_ai_keywords():
    """
    返回 AI 相关职位的关键词，用于搜索优化
    """
    return [
        # AI Agent 相关
        "AI Agent",
        "LLM",
        "Large Language Model",
        "GPT",
        "Claude",
        "AI Assistant",
        "Conversational AI",
        "AI Workflow",
        "AI Automation",

        # AI 工具相关
        "AI Tools",
        "AI Coding",
        "AI Developer Tools",
        "Copilot",
        "AI-powered",

        # 通用 AI
        "Artificial Intelligence",
        "Machine Learning",
        "Deep Learning",
        "GenAI",
        "Generative AI",
        "Foundation Model",
        "AI Platform",
        "AI Infrastructure",
        "MLOps",

        # AI 应用
        "AI Product",
        "AI Application",
        "AI SaaS"
    ]


def has_ai_agent_relevance(job: dict) -> tuple:
    """
    检查职位是否与 AI Agent 相关

    Args:
        job: 职位信息字典

    Returns:
        (is_relevant: bool, relevance_score: float 0-1)
    """
    # 合并所有文本字段
    text_fields = [
        job.get('job_title', ''),
        job.get('job_description', ''),
        ' '.join(job.get('skills_required', [])),
        ' '.join(job.get('requirements', [])),
        ' '.join(job.get('responsibilities', [])),
        job.get('company_industry', ''),
    ]
    text = ' '.join(text_fields).lower()

    # 计算匹配的关键词数量
    matches = sum(1 for kw in AI_AGENT_KEYWORDS if kw in text)

    # 5个关键词以上为满分相关性
    relevance = min(matches / 5, 1.0)

    return matches > 0, relevance


def get_skill_weights():
    """返回技能权重配置"""
    return SKILL_WEIGHTS


def get_ai_relevance_bonus_max():
    """返回 AI 相关性加分上限"""
    return AI_RELEVANCE_BONUS_MAX


if __name__ == "__main__":
    # Print profile summary
    profile = get_user_profile()
    print("=" * 60)
    print("PM Job Finder - User Profile Summary")
    print("=" * 60)
    print(f"\n👤 {profile['personal_brand']['positioning']}")
    print(f"   Twitter: {profile['personal_brand']['twitter']}")
    print(f"\n📊 Experience: {profile['years_experience']} years")
    print(f"🎯 Target Levels: {', '.join(profile['target_level'])}")
    print(f"💰 Salary Range: ${profile['salary_expectation_min']:,} - ${profile['salary_expectation_target']:,} USD")

    print(f"\n🤖 AI Agent Skills:")
    for skill in profile['ai_agent_skills'][:5]:
        print(f"   • {skill}")
    print(f"   ... and {len(profile['ai_agent_skills']) - 5} more")

    print(f"\n🏭 Top Industries (weight >= 0.9):")
    top_industries = [k for k, v in profile['preferred_industries'].items() if v >= 0.9]
    for ind in top_industries:
        print(f"   • {ind}")

    print(f"\n🌍 Remote Preference: {max(profile['location_preferences'], key=profile['location_preferences'].get)}")
    print(f"📍 Preferred Regions: {', '.join(profile['preferred_regions'][:3])}")

    print("\n" + "=" * 60)
