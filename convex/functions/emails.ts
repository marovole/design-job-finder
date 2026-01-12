import { queryGeneric, mutationGeneric } from "convex/server";
import { v } from "convex/values";

// 获取用户的邮件列表
export const getEmails = queryGeneric({
  args: {
    projectId: v.optional(v.id("projects")),
    status: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return [];

    if (args.projectId) {
      const emails = await ctx.db
        .query("generatedEmails")
        .withIndex("by_projectId", (q) => q.eq("projectId", args.projectId))
        .collect();
      return emails;
    }

    let q = ctx.db
      .query("generatedEmails")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject));

    if (args.status) {
      // 过滤状态
      const all = await q.collect();
      return all.filter((e) => e.status === args.status).slice(0, args.limit || 50);
    }

    return q.order("desc").take(args.limit || 50);
  },
});

// 获取单封邮件
export const getEmail = queryGeneric({
  args: { id: v.id("generatedEmails") },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return null;

    const email = await ctx.db.get(args.id);
    if (!email || email.userId !== identity.subject) return null;

    return email;
  },
});

// 生成个性化邮件
export const generateEmail = mutationGeneric({
  args: {
    projectId: v.id("projects"),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const [project, profile] = await Promise.all([
      ctx.db.get(args.projectId),
      ctx.db
        .query("userProfiles")
        .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
        .first(),
    ]);

    if (!project) throw new Error("Project not found");
    if (!profile) throw new Error("Profile not found");

    // 1. 分析项目需求，确定推销角度
    const analysis = analyzeProjectRequirements(project, profile);

    // 2. 匹配最佳成就
    const achievementMatch = findBestAchievement(profile.highlightProjects, project);

    // 3. 生成邮件内容
    const email = buildEmail(project, profile, analysis, achievementMatch);

    // 4. 保存邮件
    const emailId = await ctx.db.insert("generatedEmails", {
      userId: identity.subject,
      projectId: args.projectId,
      pitchAngle: analysis.pitchAngle,
      matchedAchievement: achievementMatch.achievement?.name,
      relevanceScore: analysis.score,
      subjectLines: email.subjects,
      opening: email.opening,
      valueProposition: email.valueProposition,
      socialProof: email.socialProof,
      callToAction: email.cta,
      signature: profile.emailTemplates?.signature || profile.name,
      fullEmail: email.full,
      status: "draft",
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });

    // 5. 更新项目状态
    await ctx.db.patch(args.projectId, {
      hasEmailGenerated: true,
      emailGeneratedAt: Date.now(),
      updatedAt: Date.now(),
    });

    return emailId;
  },
});

// 更新邮件状态
export const updateEmailStatus = mutationGeneric({
  args: {
    id: v.id("generatedEmails"),
    status: v.string(),
    sentAt: v.optional(v.number()),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const email = await ctx.db.get(args.id);
    if (!email || email.userId !== identity.subject) {
      throw new Error("Email not found");
    }

    await ctx.db.patch(args.id, {
      status: args.status,
      sentAt: args.sentAt || (args.status === "sent" ? Date.now() : undefined),
      updatedAt: Date.now(),
    });
  },
});

// 删除邮件
export const deleteEmail = mutationGeneric({
  args: { id: v.id("generatedEmails") },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const email = await ctx.db.get(args.id);
    if (!email || email.userId !== identity.subject) {
      throw new Error("Email not found");
    }

    await ctx.db.delete(args.id);
  },
});

// 使用 OpenRouter 免费 AI 生成邮件
export const generateEmailWithAI = mutationGeneric({
  args: {
    projectId: v.id("projects"),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const [project, profile] = await Promise.all([
      ctx.db.get(args.projectId),
      ctx.db
        .query("userProfiles")
        .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
        .first(),
    ]);

    if (!project) throw new Error("Project not found");
    if (!profile) throw new Error("Profile not found");

    const openrouterApiKey = process.env.OPENROUTER_API_KEY;
    if (!openrouterApiKey) {
      throw new Error("OPENROUTER_API_KEY not configured");
    }

    // 构建 AI prompt
    const systemPrompt = `You are an expert email copywriter specializing in job application emails.
Write professional, personalized, and compelling emails that highlight the candidate's relevant experience.
Keep the tone confident but not arrogant. Be specific about how the candidate's experience matches the job requirements.
Write in English. Keep the email concise (under 200 words).`;

    const userPrompt = `Generate a personalized job application email based on:

**Job/Project:**
- Title: ${project.title}
- Description: ${project.description?.substring(0, 500) || "N/A"}
- Platform: ${project.platform}
- Client Industry: ${project.clientIndustry || "Not specified"}

**Candidate Profile:**
- Name: ${profile.nameEn} (${profile.name})
- Role: ${profile.roleEn}
- Years of Experience: ${profile.yearsExperience}
- Core Expertise: ${profile.coreExpertise.join(", ")}
- Highlight Projects: ${profile.highlightProjects.map((p: any) => `${p.name}: ${p.result}`).join("; ")}

Generate:
1. 3 compelling subject lines (each on a new line, prefixed with "Subject: ")
2. A personalized email body that:
   - Opens with a hook related to the job
   - Highlights relevant experience with specific achievements
   - Includes a clear call-to-action
   - Ends with a professional signature

Format the output as:
SUBJECTS:
Subject: [subject 1]
Subject: [subject 2]
Subject: [subject 3]

EMAIL:
[full email body]`;

    try {
      const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${openrouterApiKey}`,
          "HTTP-Referer": "https://pm-job-finder.vercel.app",
          "X-Title": "PM Job Finder",
        },
        body: JSON.stringify({
          model: "mistralai/devstral-2512:free",
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt },
          ],
          max_tokens: 1000,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`OpenRouter API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const aiContent = data.choices?.[0]?.message?.content || "";

      // 解析 AI 响应
      const { subjects, emailBody } = parseAIResponse(aiContent, project, profile);

      // 分析推销角度
      const analysis = analyzeProjectRequirements(project, profile);
      const achievementMatch = findBestAchievement(profile.highlightProjects, project);

      // 保存邮件
      const emailId = await ctx.db.insert("generatedEmails", {
        userId: identity.subject,
        projectId: args.projectId,
        pitchAngle: analysis.pitchAngle,
        matchedAchievement: achievementMatch.achievement?.name,
        relevanceScore: analysis.score,
        subjectLines: subjects,
        opening: emailBody.split("\n\n")[0] || "",
        valueProposition: emailBody.split("\n\n")[1] || "",
        socialProof: "",
        callToAction: emailBody.split("\n\n").slice(-2, -1)[0] || "",
        signature: profile.emailTemplates?.signature || `${profile.nameEn} (${profile.name})`,
        fullEmail: `Subject: ${subjects[0]}\n\n${emailBody}`,
        status: "draft",
        createdAt: Date.now(),
        updatedAt: Date.now(),
      });

      // 更新项目状态
      await ctx.db.patch(args.projectId, {
        hasEmailGenerated: true,
        emailGeneratedAt: Date.now(),
        updatedAt: Date.now(),
      });

      return emailId;
    } catch (error: any) {
      console.error("AI email generation failed:", error);
      throw new Error(`Failed to generate AI email: ${error.message}`);
    }
  },
});

// 解析 AI 响应
function parseAIResponse(
  content: string,
  project: any,
  profile: any
): { subjects: string[]; emailBody: string } {
  const subjects: string[] = [];
  let emailBody = "";

  // 提取主题行
  const subjectMatches = content.match(/Subject:\s*(.+)/g);
  if (subjectMatches) {
    subjectMatches.forEach((match) => {
      const subject = match.replace(/Subject:\s*/, "").trim();
      if (subject && subjects.length < 3) {
        subjects.push(subject);
      }
    });
  }

  // 提取邮件正文
  const emailMatch = content.match(/EMAIL:\s*([\s\S]*)/i);
  if (emailMatch) {
    emailBody = emailMatch[1].trim();
  } else {
    // 如果没有 EMAIL: 标记，尝试提取最后一个 Subject 后的内容
    const lastSubjectIndex = content.lastIndexOf("Subject:");
    if (lastSubjectIndex !== -1) {
      const afterSubjects = content.substring(lastSubjectIndex);
      const newlineIndex = afterSubjects.indexOf("\n");
      if (newlineIndex !== -1) {
        emailBody = afterSubjects.substring(newlineIndex).trim();
      }
    }
  }

  // 如果仍然没有解析到内容，使用回退方案
  if (subjects.length === 0) {
    subjects.push(
      `${profile.roleEn} interested in: ${project.title}`,
      `Experience with ${project.clientIndustry || "your industry"} - ${project.title}`,
      `${profile.nameEn}'s application for ${project.title}`
    );
  }

  if (!emailBody) {
    emailBody = content;
  }

  return { subjects, emailBody };
}

// 分析项目需求
function analyzeProjectRequirements(
  project: any,
  profile: any
): { pitchAngle: string; score: number; needs: string[]; painPoints: string[] } {
  const text = `${project.title} ${project.description}`.toLowerCase();
  const needs: string[] = [];
  const painPoints: string[] = [];
  let score = 0;
  let pitchAngle = "default";

  // 检测需求类型
  if (text.includes("dashboard") || text.includes("analytics") || text.includes("data")) {
    needs.push("数据分析");
    painPoints.push("数据可视化复杂");
    pitchAngle = "analytics";
    score += 40;
  }

  if (text.includes("b2b") || text.includes("saas") || text.includes("enterprise")) {
    needs.push("B2B/企业产品");
    painPoints.push("用户体验复杂");
    pitchAngle = "b2b";
    score += 35;
  }

  if (text.includes("merchant") || text.includes("business") || text.includes("commerce")) {
    needs.push("商家/商业产品");
    painPoints.push("多角色权限管理");
    pitchAngle = "merchant";
    score += 30;
  }

  if (text.includes("mobile") || text.includes("app")) {
    needs.push("移动端设计");
    painPoints.push("跨平台一致性");
    score += 25;
  }

  if (text.includes("design system") || text.includes("component")) {
    needs.push("设计系统");
    painPoints.push("组件标准化");
    score += 20;
  }

  // 行业匹配
  const industries = profile.preferredIndustries;
  if (industries.highPriority.some((i: string) => text.includes(i.toLowerCase()))) {
    score += 30;
  }

  return { pitchAngle, score, needs, painPoints };
}

// 查找最佳成就匹配
function findBestAchievement(
  achievements: any[],
  project: any
): { achievement: any; score: number } {
  const text = `${project.title} ${project.description}`.toLowerCase();
  let bestMatch = { achievement: null as any, score: 0 };

  for (const achievement of achievements) {
    let matchScore = 0;
    for (const keyword of achievement.keywords || []) {
      if (text.includes(keyword.toLowerCase())) {
        matchScore += 10;
      }
    }
    if (matchScore > bestMatch.score) {
      bestMatch = { achievement, score: matchScore };
    }
  }

  return bestMatch;
}

// 构建邮件内容
function buildEmail(
  project: any,
  profile: any,
  analysis: { pitchAngle: string; score: number; needs: string[] },
  achievementMatch: { achievement: any; score: number }
): { subjects: string[]; opening: string; valueProposition: string; socialProof: string; cta: string; full: string } {
  const templates = profile.emailTemplates || {};

  // 选择开场白
  let opening = templates.defaultOpener || `With ${profile.yearsExperience}+ years in UX design, including ${profile.yearsExperience - 4} years at Huawei working on enterprise-scale platforms, I bring deep expertise in complex system design.`;

  if (analysis.pitchAngle === "analytics" && templates.analyticsOpener) {
    opening = templates.analyticsOpener.replace("{project_title}", project.title);
  } else if (analysis.pitchAngle === "b2b" && templates.b2bOpener) {
    opening = templates.b2bOpener;
  } else if (analysis.pitchAngle === "merchant" && templates.merchantOpener) {
    opening = templates.merchantOpener;
  }

  // 价值主张
  let valueProposition = "";
  if (achievementMatch.achievement) {
    valueProposition = `I specifically worked on ${achievementMatch.achievement.name} - ${achievementMatch.achievement.result} - which directly relates to your need for ${analysis.needs.join(", ")}.`;
  } else {
    valueProposition = `My expertise in ${profile.coreExpertise.slice(0, 3).join(", ")} enables me to deliver high-quality solutions for your project.`;
  }

  // 社会证明
  let socialProof = "";
  if (achievementMatch.achievement?.benchmark) {
    socialProof = `This project was benchmarked against ${achievementMatch.achievement.benchmark}.`;
  }

  // 行动号召
  let cta = templates.fulltimeCta || "I'd welcome the opportunity to discuss how my experience could contribute to your team.";
  if (profile.workPreference.acceptsProjectBased && profile.workPreference.acceptsRemote) {
    cta = templates.parttimeCta || templates.remoteCta || cta;
  }

  // 签名
  const signature = templates.signature || `${profile.nameEn} (${profile.name})\n${profile.role}`;

  // 生成主题行
  const subjects = [
    `${profile.role} interested in: ${project.title}`,
    `Experience with ${analysis.needs[0] || "similar projects"} - ${project.title}`,
    `${profile.nameEn}'s application for ${project.title}`,
  ];

  // 组装完整邮件
  const full = `Subject: ${subjects[0]}

${opening}

${valueProposition}

${socialProof}${socialProof ? "\n" : ""}${project.description?.substring(0, 200)}...

${cta}

${signature}

---
Portfolio: ${profile.website || ""}
Email: ${profile.email}
`;

  return { subjects, opening, valueProposition, socialProof, cta, full };
}
