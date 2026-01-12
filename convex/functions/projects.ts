import { queryGeneric, mutationGeneric } from "convex/server";
import { v } from "convex/values";

// 获取用户项目列表
export const getProjects = queryGeneric({
  args: {
    platform: v.optional(v.string()),
    minScore: v.optional(v.number()),
    hasEmail: v.optional(v.boolean()),
    limit: v.optional(v.number()),
    cursor: v.optional(v.id("projects")),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return { projects: [], continuation: null };

    let q = ctx.db
      .query("projects")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject));

    const results = await q.take(args.limit || 50);

    // 过滤
    let filtered = results;
    if (args.platform) {
      filtered = filtered.filter((p) => p.platform === args.platform);
    }
    if (args.minScore !== undefined) {
      filtered = filtered.filter((p) => (p.matchScore || 0) >= args.minScore!);
    }
    if (args.hasEmail !== undefined) {
      filtered = filtered.filter((p) => p.hasEmailGenerated === args.hasEmail);
    }

    return { projects: filtered, continuation: null };
  },
});

// 获取单个项目
export const getProject = queryGeneric({
  args: { id: v.id("projects") },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return null;

    const project = await ctx.db.get(args.id);
    if (!project || project.userId !== identity.subject) return null;

    return project;
  },
});

// 保存项目
export const saveProject = mutationGeneric({
  args: {
    id: v.optional(v.id("projects")),
    externalId: v.optional(v.string()),
    platform: v.string(),
    projectUrl: v.optional(v.string()),
    title: v.string(),
    description: v.string(),
    requirements: v.optional(v.string()),
    budgetRange: v.optional(v.string()),
    budgetMin: v.optional(v.number()),
    budgetMax: v.optional(v.number()),
    budgetCurrency: v.optional(v.string()),
    clientName: v.optional(v.string()),
    clientType: v.optional(v.string()),
    clientIndustry: v.optional(v.string()),
    clientWebsite: v.optional(v.string()),
    clientLinkedIn: v.optional(v.string()),
    clientEmail: v.optional(v.string()),
    publishedAt: v.optional(v.string()),
    tags: v.array(v.string()),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const { id, ...projectData } = args;

    if (id) {
      const existing = await ctx.db.get(id);
      if (!existing || existing.userId !== identity.subject) {
        throw new Error("Project not found");
      }
      await ctx.db.patch(id, {
        ...projectData,
        updatedAt: Date.now(),
      });
      return id;
    }

    return await ctx.db.insert("projects", {
      ...projectData,
      userId: identity.subject,
      matchScore: 0,
      emailValid: "unknown",
      urlValid: "unknown",
      hasEmailGenerated: false,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });
  },
});

// 更新项目匹配分数
export const updateMatchScore = mutationGeneric({
  args: {
    id: v.id("projects"),
    matchScore: v.number(),
    matchReasons: v.array(v.string()),
    priorityScore: v.optional(v.number()),
    priorityLabel: v.optional(v.string()),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const project = await ctx.db.get(args.id);
    if (!project || project.userId !== identity.subject) {
      throw new Error("Project not found");
    }

    await ctx.db.patch(args.id, {
      matchScore: args.matchScore,
      matchReasons: args.matchReasons,
      priorityScore: args.priorityScore,
      priorityLabel: args.priorityLabel,
      updatedAt: Date.now(),
    });
  },
});

// 批量更新匹配分数
export const batchUpdateMatchScores = mutationGeneric({
  args: {
    updates: v.array(v.object({
      id: v.id("projects"),
      matchScore: v.number(),
      matchReasons: v.array(v.string()),
      priorityScore: v.optional(v.number()),
      priorityLabel: v.optional(v.string()),
    })),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    for (const update of args.updates) {
      const project = await ctx.db.get(update.id);
      if (!project || project.userId !== identity.subject) continue;

      await ctx.db.patch(update.id, {
        matchScore: update.matchScore,
        matchReasons: update.matchReasons,
        priorityScore: update.priorityScore,
        priorityLabel: update.priorityLabel,
        updatedAt: Date.now(),
      });
    }
  },
});

// 删除项目
export const deleteProject = mutationGeneric({
  args: { id: v.id("projects") },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const project = await ctx.db.get(args.id);
    if (!project || project.userId !== identity.subject) {
      throw new Error("Project not found");
    }

    await ctx.db.delete(args.id);
  },
});

// 获取项目统计
export const getProjectStats = queryGeneric({
  args: {},
  async handler(ctx) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return null;

    const projects = await ctx.db
      .query("projects")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .collect();

    const stats = {
      total: projects.length,
      byPlatform: {} as Record<string, number>,
      avgScore: 0,
      withEmail: 0,
      validated: 0,
    };

    let totalScore = 0;
    projects.forEach((p) => {
      stats.byPlatform[p.platform] = (stats.byPlatform[p.platform] || 0) + 1;
      if (p.matchScore) totalScore += p.matchScore;
      if (p.hasEmailGenerated) stats.withEmail++;
      if (p.emailValid === "valid") stats.validated++;
    });

    stats.avgScore = projects.length > 0 ? totalScore / projects.length : 0;

    return stats;
  },
});
