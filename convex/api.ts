// Convex API exports - re-export all functions from individual modules
import { getProfile, saveProfile, createDefaultProfile, deleteProfile } from "./functions/profile";
import {
  getProjects, getProject, saveProject, updateMatchScore,
  batchUpdateMatchScores, deleteProject, getProjectStats
} from "./functions/projects";
import {
  searchProjects, calculateMatchScores, getSearchHistory, clearCache
} from "./functions/search";
import { getEmails, getEmail, generateEmail, updateEmailStatus, deleteEmail } from "./functions/emails";

export const api = {
  functions: {
    profile: {
      getProfile,
      saveProfile,
      createDefaultProfile,
      deleteProfile,
    },
    projects: {
      getProjects,
      getProject,
      saveProject,
      updateMatchScore,
      batchUpdateMatchScores,
      deleteProject,
      getProjectStats,
    },
    search: {
      searchProjects,
      calculateMatchScores,
      getSearchHistory,
      clearCache,
    },
    emails: {
      getEmails,
      getEmail,
      generateEmail,
      updateEmailStatus,
      deleteEmail,
    },
  },
};
