import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // 用户画像 - 核心配置
  userProfiles: defineTable({
    userId: v.string(),
    name: v.string(),
    nameEn: v.string(),
    email: v.string(),
    website: v.optional(v.string()),
    phone: v.optional(v.string()),
    role: v.string(),
    roleEn: v.string(),
    yearsExperience: v.number(),
    education: v.optional(v.string()),

    // 核心专长（关键词匹配用）
    coreExpertise: v.array(v.string()),
    expertiseKeywords: v.object({
      highMatch: v.array(v.string()),
      mediumMatch: v.array(v.string()),
    }),

    // 高亮项目（邮件个性化用）
    highlightProjects: v.array(v.object({
      name: v.string(),
      nameCn: v.optional(v.string()),
      benchmark: v.optional(v.string()),
      result: v.string(),
      resultEn: v.optional(v.string()),
      keywords: v.array(v.string()),
    })),

    // 偏好设置
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

    // 技能
    skills: v.object({
      designTools: v.array(v.string()),
      prototyping: v.array(v.string()),
      aiTools: v.optional(v.array(v.string())),
      dTools: v.optional(v.array(v.string())),
    }),

    // 邮件模板
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

    updatedAt: v.number(),
  }).index("by_userId", ["userId"]),

  // 搜索历史
  searchHistory: defineTable({
    userId: v.string(),
    query: v.string(),
    platforms: v.array(v.string()),
    filters: v.optional(v.object({
      budgetMin: v.optional(v.number()),
      budgetMax: v.optional(v.number()),
      clientType: v.optional(v.string()),
    })),
    resultCount: v.number(),
    createdAt: v.number(),
  }).index("by_userId", ["userId"]).index("by_createdAt", ["createdAt"]),

  // 项目/职位数据
  projects: defineTable({
    userId: v.string(),
    externalId: v.optional(v.string()),
    platform: v.string(),
    projectUrl: v.optional(v.string()),
    title: v.string(),
    description: v.string(),
    requirements: v.optional(v.string()),

    // 预算
    budgetRange: v.optional(v.string()),
    budgetMin: v.optional(v.number()),
    budgetMax: v.optional(v.number()),
    budgetCurrency: v.optional(v.string()),

    // 客户信息
    clientName: v.optional(v.string()),
    clientType: v.optional(v.string()),
    clientIndustry: v.optional(v.string()),
    clientWebsite: v.optional(v.string()),
    clientLinkedIn: v.optional(v.string()),
    clientEmail: v.optional(v.string()),
    clientReputation: v.optional(v.number()),
    clientPastProjects: v.optional(v.number()),

    // 项目状态
    status: v.optional(v.string()),
    publishedAt: v.optional(v.string()),

    // 匹配分数
    matchScore: v.optional(v.number()),
    matchReasons: v.optional(v.array(v.string())),

    // 验证结果
    emailValid: v.optional(v.string()),
    urlValid: v.optional(v.string()),
    lastVerifiedAt: v.optional(v.number()),

    // 优先级
    priorityScore: v.optional(v.number()),
    priorityLabel: v.optional(v.string()),

    // 邮件生成状态
    hasEmailGenerated: v.boolean(),
    emailGeneratedAt: v.optional(v.number()),

    // 标签
    tags: v.array(v.string()),

    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_userId", ["userId"])
    .index("by_platform", ["platform"])
    .index("by_priority", ["userId", "priorityScore"])
    .index("by_createdAt", ["createdAt"]),

  // 生成的邮件
  generatedEmails: defineTable({
    userId: v.string(),
    projectId: v.id("projects"),
    pitchAngle: v.string(),
    matchedAchievement: v.optional(v.string()),
    relevanceScore: v.number(),
    subjectLines: v.array(v.string()),
    opening: v.string(),
    valueProposition: v.optional(v.string()),
    socialProof: v.optional(v.string()),
    callToAction: v.string(),
    signature: v.string(),
    fullEmail: v.string(),
    status: v.string(),
    sentAt: v.optional(v.number()),
    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_userId", ["userId"])
    .index("by_projectId", ["projectId"])
    .index("by_status", ["userId", "status"]),

  // Exa API 缓存
  exaSearchCache: defineTable({
    queryHash: v.string(),
    query: v.string(),
    platforms: v.array(v.string()),
    filters: v.optional(v.any()),
    results: v.array(v.object({
      externalId: v.optional(v.string()),
      platform: v.string(),
      title: v.string(),
      url: v.optional(v.string()),
      data: v.any(),
    })),
    expiresAt: v.number(),
  }).index("by_queryHash", ["queryHash"]),
});
