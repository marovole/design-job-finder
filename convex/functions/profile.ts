import { queryGeneric, mutationGeneric } from "convex/server";
import { v } from "convex/values";

// 获取当前用户画像
export const getProfile = queryGeneric({
  args: {},
  async handler(ctx) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return null;

    const profile = await ctx.db
      .query("userProfiles")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .first();

    return profile;
  },
});

// 创建或更新用户画像
export const saveProfile = mutationGeneric({
  args: {
    name: v.string(),
    nameEn: v.string(),
    email: v.string(),
    website: v.optional(v.string()),
    phone: v.optional(v.string()),
    role: v.string(),
    roleEn: v.string(),
    yearsExperience: v.number(),
    education: v.optional(v.string()),
    coreExpertise: v.array(v.string()),
    expertiseKeywords: v.object({
      highMatch: v.array(v.string()),
      mediumMatch: v.array(v.string()),
    }),
    highlightProjects: v.array(v.object({
      name: v.string(),
      nameCn: v.optional(v.string()),
      benchmark: v.optional(v.string()),
      result: v.string(),
      resultEn: v.optional(v.string()),
      keywords: v.array(v.string()),
    })),
    preferredIndustries: v.object({
      highPriority: v.array(v.string()),
      mediumPriority: v.array(v.string()),
    }),
    preferredClientTypes: v.object({
      highPriority: v.array(v.string()),
      mediumPriority: v.array(v.string()),
    }),
    workPreference: v.object({
      timezone: v.string(),
      location: v.string(),
      acceptsRemote: v.boolean(),
      acceptsProjectBased: v.boolean(),
      salaryRange: v.object({
        min: v.number(),
        max: v.number(),
        currency: v.string(),
      }),
    }),
    skills: v.object({
      designTools: v.array(v.string()),
      prototyping: v.array(v.string()),
      aiTools: v.optional(v.array(v.string())),
      dTools: v.optional(v.array(v.string())),
    }),
    emailTemplates: v.optional(v.object({
      analyticsOpener: v.optional(v.string()),
      b2bOpener: v.optional(v.string()),
      merchantOpener: v.optional(v.string()),
      defaultOpener: v.optional(v.string()),
      parttimeNote: v.optional(v.string()),
      parttimeCta: v.optional(v.string()),
      remoteCta: v.optional(v.string()),
      fulltimeCta: v.optional(v.string()),
      signature: v.optional(v.string()),
    })),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const existing = await ctx.db
      .query("userProfiles")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        ...args,
        updatedAt: Date.now(),
      });
      return existing._id;
    }

    return await ctx.db.insert("userProfiles", {
      ...args,
      userId: identity.subject,
      updatedAt: Date.now(),
    });
  },
});

// 从 YAML 配置创建默认画像（首次登录）
export const createDefaultProfile = mutationGeneric({
  args: {},
  async handler(ctx) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const existing = await ctx.db
      .query("userProfiles")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .first();

    if (existing) return existing._id;

    return await ctx.db.insert("userProfiles", {
      userId: identity.subject,
      name: identity.name || "New User",
      nameEn: identity.name || "New User",
      email: identity.email || "",
      role: "UX Designer",
      roleEn: "UX Designer",
      yearsExperience: 5,
      coreExpertise: [],
      expertiseKeywords: {
        highMatch: [],
        mediumMatch: [],
      },
      highlightProjects: [],
      preferredIndustries: {
        highPriority: [],
        mediumPriority: [],
      },
      preferredClientTypes: {
        highPriority: [],
        mediumPriority: [],
      },
      workPreference: {
        timezone: "UTC+8",
        location: "China",
        acceptsRemote: true,
        acceptsProjectBased: true,
        salaryRange: { min: 0, max: 50000, currency: "CNY" },
      },
      skills: {
        designTools: [],
        prototyping: [],
      },
      updatedAt: Date.now(),
    });
  },
});

// 删除用户画像
export const deleteProfile = mutationGeneric({
  args: {},
  async handler(ctx) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const profile = await ctx.db
      .query("userProfiles")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .first();

    if (profile) {
      await ctx.db.delete(profile._id);
    }
  },
});
