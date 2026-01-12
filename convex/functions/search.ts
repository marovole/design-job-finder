import { queryGeneric, mutationGeneric } from "convex/server";
import { v } from "convex/values";

// 生成查询哈希用于缓存
async function getQueryHash(query: string, platforms: string[], filters?: {
  budgetMin?: number;
  budgetMax?: number;
  clientType?: string;
}): Promise<string> {
  const data = JSON.stringify({ query, platforms, filters });
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);
  // Use Web Crypto API directly
  const hashBuffer = await crypto.subtle.digest("SHA-256", dataBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

// 搜索项目
export const searchProjects = mutationGeneric({
  args: {
    query: v.string(),
    platforms: v.array(v.string()),
    budgetMin: v.optional(v.number()),
    budgetMax: v.optional(v.number()),
    clientType: v.optional(v.string()),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    // 1. 检查缓存
    const queryHash = await getQueryHash(args.query, args.platforms, {
      budgetMin: args.budgetMin,
      budgetMax: args.budgetMax,
      clientType: args.clientType,
    });

    const cached = await ctx.db
      .query("exaSearchCache")
      .withIndex("by_queryHash", (q) => q.eq("queryHash", queryHash))
      .first();

    if (cached && cached.expiresAt > Date.now()) {
      // 记录搜索历史
      await ctx.db.insert("searchHistory", {
        userId: identity.subject,
        query: args.query,
        platforms: args.platforms,
        filters: {
          budgetMin: args.budgetMin,
          budgetMax: args.budgetMax,
          clientType: args.clientType,
        },
        resultCount: cached.results.length,
        createdAt: Date.now(),
      });
      return { projects: cached.results, fromCache: true };
    }

    // 2. 调用 Exa API (通过环境变量中的 API 密钥)
    const exaApiKey = process.env.EXA_API_KEY;
    if (!exaApiKey) {
      throw new Error("EXA_API_KEY not configured");
    }

    const searchResults = await searchExa(args, exaApiKey);

    // 3. 缓存结果 (24小时过期)
    await ctx.db.insert("exaSearchCache", {
      queryHash,
      query: args.query,
      platforms: args.platforms,
      filters: {
        budgetMin: args.budgetMin,
        budgetMax: args.budgetMax,
        clientType: args.clientType,
      },
      results: searchResults,
      expiresAt: Date.now() + 24 * 60 * 60 * 1000,
    });

    // 4. 记录搜索历史
    await ctx.db.insert("searchHistory", {
      userId: identity.subject,
      query: args.query,
      platforms: args.platforms,
      filters: {
        budgetMin: args.budgetMin,
        budgetMax: args.budgetMax,
        clientType: args.clientType,
      },
      resultCount: searchResults.length,
      createdAt: Date.now(),
    });

    return { projects: searchResults, fromCache: false };
  },
});

// Exa API 调用
async function searchExa(args: {
  query: string;
  platforms: string[];
  budgetMin?: number;
  budgetMax?: number;
  clientType?: string;
}, apiKey: string) {
  // 构建 Exa 查询
  const queries: string[] = [];

  args.platforms.forEach((platform) => {
    switch (platform) {
      case "fiverr":
        queries.push(`${args.query} site:fiverr.com`);
        break;
      case "upwork":
        queries.push(`${args.query} site:upwork.com`);
        break;
      case "dribbble":
        queries.push(`${args.query} site:dribbble.com`);
        break;
      case "linkedin":
        queries.push(`${args.query} site:linkedin.com`);
        break;
    }
  });

  const response = await fetch("https://api.exa.ai/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
    },
    body: JSON.stringify({
      query: queries.join(" OR "),
      numResults: 50,
      filters: {
        type: "web",
        startPublishedDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Exa API error: ${response.statusText}`);
  }

  const data = await response.json();

  // 解析结果
  return data.results.map((result: any) => ({
    externalId: result.id,
    platform: detectPlatform(result.url),
    title: result.title,
    url: result.url,
    description: result.text?.substring(0, 500),
    publishedAt: result.publishedDate,
  }));
}

// 从 URL 检测平台
function detectPlatform(url: string): string {
  if (url.includes("fiverr.com")) return "fiverr";
  if (url.includes("upwork.com")) return "upwork";
  if (url.includes("dribbble.com")) return "dribbble";
  if (url.includes("linkedin.com")) return "linkedin";
  if (url.includes("angel.co") || url.includes("wellfound.com")) return "angel";
  if (url.includes("remoteok.io")) return "remoteok";
  return "other";
}

// 计算匹配分数
export const calculateMatchScores = mutationGeneric({
  args: {
    projects: v.array(v.object({
      id: v.optional(v.id("projects")),
      title: v.string(),
      description: v.string(),
      budget: v.optional(v.number()),
      industry: v.optional(v.string()),
      clientType: v.optional(v.string()),
    })),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    const profile = await ctx.db
      .query("userProfiles")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .first();

    if (!profile) throw new Error("Profile not found");

    const results = args.projects.map((project) => {
      let score = 0;
      const reasons: string[] = [];
      const combinedText = `${project.title} ${project.description}`.toLowerCase();
      const keywords = profile.expertiseKeywords;

      // 关键词匹配 (40分)
      keywords.highMatch.forEach((kw: string) => {
        if (combinedText.includes(kw.toLowerCase())) {
          score += 10;
          reasons.push(`匹配关键词: ${kw}`);
        }
      });

      keywords.mediumMatch.forEach((kw: string) => {
        if (combinedText.includes(kw.toLowerCase())) {
          score += 5;
          reasons.push(`部分匹配: ${kw}`);
        }
      });

      // 行业匹配 (30分)
      const industries = profile.preferredIndustries;
      industries.highPriority.forEach((ind: string) => {
        if ((project.industry || "").toLowerCase().includes(ind.toLowerCase())) {
          score += 30;
          reasons.push(`优先行业: ${ind}`);
        }
      });

      industries.mediumPriority.forEach((ind: string) => {
        if ((project.industry || "").toLowerCase().includes(ind.toLowerCase())) {
          score += 15;
          reasons.push(`中等行业: ${ind}`);
        }
      });

      // 客户类型匹配 (20分)
      const clientTypes = profile.preferredClientTypes;
      if (project.clientType) {
        if (clientTypes.highPriority.includes(project.clientType)) {
          score += 20;
          reasons.push(`优先客户类型: ${project.clientType}`);
        } else if (clientTypes.mediumPriority.includes(project.clientType)) {
          score += 10;
          reasons.push(`中等客户类型: ${project.clientType}`);
        }
      }

      // 预算匹配 (10分)
      if (project.budget) {
        if (project.budget >= 2000) {
          score += 10;
          reasons.push("预算符合期望 (>= $2000)");
        } else if (project.budget >= 1000) {
          score += 5;
          reasons.push("预算中等 (>= $1000)");
        }
      }

      // 计算优先级分数
      const priorityScore = score * 100;
      let priorityLabel = "D";
      if (score >= 80) priorityLabel = "A";
      else if (score >= 60) priorityLabel = "B";
      else if (score >= 40) priorityLabel = "C";

      return {
        ...project,
        matchScore: Math.min(score, 100),
        matchReasons: reasons,
        priorityScore,
        priorityLabel,
      };
    });

    return results;
  },
});

// 获取搜索历史
export const getSearchHistory = queryGeneric({
  args: {
    limit: v.optional(v.number()),
  },
  async handler(ctx, args) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return [];

    const history = await ctx.db
      .query("searchHistory")
      .withIndex("by_userId", (q) => q.eq("userId", identity.subject))
      .order("desc")
      .take(args.limit || 20);

    return history;
  },
});

// 清除缓存
export const clearCache = mutationGeneric({
  args: {},
  async handler(ctx) {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthorized");

    // 只清除该用户的缓存
    const cache = await ctx.db.query("exaSearchCache").collect();
    for (const item of cache) {
      await ctx.db.delete(item._id);
    }
  },
});
