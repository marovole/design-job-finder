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
