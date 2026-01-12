from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Project:
    name: str
    description: str
    tech_stack: List[str]
    outcome: str

@dataclass
class FreelancerProfile:
    name: str = "Marovole"  # Placeholder
    title: str = "Full-stack Product Engineer"

    # Core Value Prop
    pitch_one_liner: str = "I turn fuzzy requirements into shipped products (Web/App) in weeks, not months."

    # Technical Capability
    tech_stack: Dict[str, List[str]] = None

    # Product Capability
    pm_skills: List[str] = None

    # Portfolio
    highlight_projects: List[Project] = None

    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = {
                "Frontend": ["Next.js", "React", "TailwindCSS", "TypeScript", "React Native"],
                "Backend": ["Python", "FastAPI", "Node.js", "Convex", "PostgreSQL"],
                "DevOps": ["Vercel", "Docker", "AWS", "CI/CD"],
                "AI": ["LangChain", "OpenAI API", "Claude SDK"]
            }

        if self.pm_skills is None:
            self.pm_skills = [
                "0-1 MVP Strategy",
                "Product Discovery",
                "User Story Mapping",
                "Technical Architecture Design",
                "Go-to-Market Support"
            ]

        if self.highlight_projects is None:
            self.highlight_projects = [
                Project(
                    name="SaaS MVP Builder",
                    description="Independent full-stack development of a B2B SaaS platform.",
                    tech_stack=["Next.js", "FastAPI", "Stripe"],
                    outcome="Launched in 3 weeks, secured first 10 paying users."
                ),
                Project(
                    name="AI Agent Workflow",
                    description="Complex workflow automation system for data processing.",
                    tech_stack=["Python", "LangGraph", "React"],
                    outcome="Reduced manual processing time by 80%."
                )
            ]

# Singleton instance
USER_PROFILE = FreelancerProfile()
