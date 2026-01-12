# 部署指南

## 1. 登录 Convex

在你的终端中运行：

```bash
cd /Users/marovole/conductor/workspaces/PM-job-finder/chengdu
npx convex login
```

这会打开浏览器让你登录 Convex 账户。

## 2. 配置环境变量

编辑 `.env.local`，填入完整的凭证：

```env
# Convex URL (部署后自动填充)
NEXT_PUBLIC_CONVEX_URL=

# GitHub OAuth (在 https://github.com/settings/developers 创建)
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# Exa API (在 https://exa.ai 获取)
EXA_API_KEY=your-exa-api-key
```

## 3. 启动开发模式

```bash
npx convex dev
```

这会：
- 创建 Convex 项目
- 生成类型定义
- 启动实时开发服务器

## 4. 启动前端

在另一个终端：

```bash
npm run dev
```

访问 http://localhost:3000

## 5. 部署到生产环境

```bash
# 部署 Convex 后端
npx convex deploy

# 部署前端 (Vercel)
npx vercel --prod
```

## GitHub OAuth 配置

1. 访问 https://github.com/settings/developers
2. New OAuth App:
   - Application name: PM Job Finder
   - Homepage URL: http://localhost:3000
   - Authorization callback URL: http://localhost:3000/api/auth/callback/github
3. 复制 Client ID 和 Client Secret 到 `.env.local`
