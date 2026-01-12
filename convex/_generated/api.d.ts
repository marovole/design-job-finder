/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as api_ from "../api.js";
import type * as auth from "../auth.js";
import type * as functions__generated from "../functions/_generated.js";
import type * as functions_emails from "../functions/emails.js";
import type * as functions_profile from "../functions/profile.js";
import type * as functions_projects from "../functions/projects.js";
import type * as functions_search from "../functions/search.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  api: typeof api_;
  auth: typeof auth;
  "functions/_generated": typeof functions__generated;
  "functions/emails": typeof functions_emails;
  "functions/profile": typeof functions_profile;
  "functions/projects": typeof functions_projects;
  "functions/search": typeof functions_search;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
