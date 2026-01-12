from hybrid_analyzer import ProjectAnalysis, ProjectStage
from profile import USER_PROFILE

class OutreachGenerator:
    def generate(self, analysis: ProjectAnalysis) -> str:
        # Determine the angle
        if analysis.is_fuzzy or 'fuzzy_requirements' in analysis.pain_points:
            return self._generate_consulting_pitch(analysis)
        elif 'missing_cto' in analysis.pain_points:
            return self._generate_cto_pitch(analysis)
        elif analysis.project_stage == ProjectStage.GREENFIELD:
            return self._generate_mvp_pitch(analysis)
        else:
            return self._generate_general_pitch(analysis)

    def _generate_mvp_pitch(self, analysis: ProjectAnalysis) -> str:
        tech_list = ", ".join(USER_PROFILE.tech_stack['Frontend'][:2] + USER_PROFILE.tech_stack['Backend'][:2])
        return f"""
Subject: Rapid MVP development for {analysis.project_title}

Hi {analysis.client_name or 'there'},

I saw your post about {analysis.project_title} and noticed you're looking to launch a new product from scratch.

I am a {USER_PROFILE.title} specializing in 0-1 MVP delivery. Unlike typical agencies or siloed freelancers, I handle the full cycle: from product definition (PRD/Roadmap) to shipping production code.

My stack is built for speed: {tech_list}.

One of my recent projects, {USER_PROFILE.highlight_projects[0].name}, was {USER_PROFILE.highlight_projects[0].outcome}.

I'd love to help you validate this idea fast.

Best,
{USER_PROFILE.name}
{USER_PROFILE.pitch_one_liner}
"""

    def _generate_consulting_pitch(self, analysis: ProjectAnalysis) -> str:
        return f"""
Subject: Turning your idea for {analysis.project_title} into a live product

Hi {analysis.client_name or 'there'},

I noticed you have a vision for {analysis.project_title} but might need help fleshing out the technical requirements.

I bridge the gap between Product Manager and Lead Developer. I can help you clarify the scope, define the MVP features, and then build the actual application myself. No "lost in translation" between business and tech.

I recently helped a client {USER_PROFILE.highlight_projects[1].outcome} by handling both the workflow design and implementation.

Let's chat about getting this off the ground.

Best,
{USER_PROFILE.name}
"""

    def _generate_cto_pitch(self, analysis: ProjectAnalysis) -> str:
        return f"""
Subject: Technical partner for {analysis.project_title}

Hi {analysis.client_name or 'there'},

It sounds like you need more than just a coder—you need a technical partner who understands the business goals.

I work as a Fractional CTO / Senior Product Engineer for early-stage founders. I can handle your architecture, stack selection ({", ".join(USER_PROFILE.tech_stack['Backend'])}), and deployment.

I've built and launched SaaS products independently (e.g., {USER_PROFILE.highlight_projects[0].name}), so I know the pitfalls to avoid.

Happy to share more if you're interested.

Best,
{USER_PROFILE.name}
"""

    def _generate_general_pitch(self, analysis: ProjectAnalysis) -> str:
        return f"""
Subject: Full-stack assistance for {analysis.project_title}

Hi {analysis.client_name or 'there'},

I saw you are looking for help with {analysis.project_title}.

I am a Full-stack Product Engineer with experience in {", ".join(analysis.dev_needs) if analysis.dev_needs else "modern web stacks"}.

I bring a product-first mindset to coding, ensuring what we build actually solves the user problem.

Best,
{USER_PROFILE.name}
"""

def generate_email(analysis: ProjectAnalysis) -> str:
    return OutreachGenerator().generate(analysis)
