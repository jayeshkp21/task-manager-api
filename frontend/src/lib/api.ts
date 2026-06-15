// frontend/src/lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://task-manager-api.onrender.com"

function getToken(type: "access_token" | "refresh_token" = "access_token") {
  if (typeof window !== "undefined") {
    return localStorage.getItem(type)
  }
  return null
}

async function request(endpoint: string, options: RequestInit = {}) {
  const token = getToken("access_token")
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  // Automatic logout if token is unauthorized
  if (response.status === 401 && !endpoint.includes("/auth/login") && !endpoint.includes("/auth/signup")) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      window.location.href = "/login"
    }
    return response
  }

  return response
}

export const api = {
  // ── Authentication ────────────────────────────────────────────────
  signup: (data: object) =>
    request("/auth/signup", { method: "POST", body: JSON.stringify(data) }),

  login: (data: object) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(data) }),

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
    }
    return request("/auth/logout")
  },

  me: () => request("/auth/me"),

  refreshToken: () => {
    const refresh = getToken("refresh_token")
    return request("/auth/refresh_token", {
      headers: {
        Authorization: `Bearer ${refresh}`
      }
    })
  },

  passwordReset: (data: { email: string }) =>
    request("/auth/password_reset", { method: "POST", body: JSON.stringify(data) }),

  passwordResetConfirm: (token: string, data: object) =>
    request(`/auth/password-reset-confirm/${token}`, { method: "POST", body: JSON.stringify(data) }),

  searchUsers: (query: string) =>
    request(`/auth/users/search?q=${encodeURIComponent(query)}`),

  // ── Projects ──────────────────────────────────────────────────────
  getAllProjects: (page = 1, pageSize = 20) =>
    request(`/projects/?page=${page}&page_size=${pageSize}`),

  getMyProjects: (page = 1, pageSize = 20) =>
    request(`/projects/mine?page=${page}&page_size=${pageSize}`),

  getProject: (uid: string) =>
    request(`/projects/${uid}`),

  createProject: (data: object) =>
    request("/projects/", { method: "POST", body: JSON.stringify(data) }),

  updateProject: (uid: string, data: object) =>
    request(`/projects/${uid}`, { method: "PATCH", body: JSON.stringify(data) }),

  deleteProject: (uid: string) =>
    request(`/projects/${uid}`, { method: "DELETE" }),

  getProjectStats: (uid: string) =>
    request(`/projects/${uid}/stats`),

  getProjectMembers: (uid: string, page = 1, pageSize = 20) =>
    request(`/projects/${uid}/members?page=${page}&page_size=${pageSize}`),

  addMember: (projectUid: string, data: object) =>
    request(`/projects/${projectUid}/members`, { method: "POST", body: JSON.stringify(data) }),

  removeMember: (projectUid: string, userUid: string) =>
    request(`/projects/${projectUid}/members/${userUid}`, { method: "DELETE" }),

  updateMemberRole: (projectUid: string, userUid: string, data: object) =>
    request(`/projects/${projectUid}/members/${userUid}`, { method: "PATCH", body: JSON.stringify(data) }),

  // ── Tasks ─────────────────────────────────────────────────────────
  getProjectTasks: (projectUid: string, params?: Record<string, string>) => {
    const query = new URLSearchParams(params || {}).toString()
    return request(`/tasks/projects/${projectUid}/tasks${query ? "?" + query : ""}`)
  },

  getTask: (projectUid: string, taskUid: string) =>
    request(`/tasks/projects/${projectUid}/tasks/${taskUid}`),

  createTask: (projectUid: string, data: object) =>
    request(`/tasks/projects/${projectUid}/tasks`, { method: "POST", body: JSON.stringify(data) }),

  updateTask: (projectUid: string, taskUid: string, data: object) =>
    request(`/tasks/projects/${projectUid}/tasks/${taskUid}`, { method: "PATCH", body: JSON.stringify(data) }),

  deleteTask: (projectUid: string, taskUid: string) =>
    request(`/tasks/projects/${projectUid}/tasks/${taskUid}`, { method: "DELETE" }),

  getTaskActivity: (projectUid: string, taskUid: string) =>
    request(`/tasks/projects/${projectUid}/tasks/${taskUid}/activity`),

  getMyTasks: (status?: string) => {
    const query = status ? `?status=${status}` : ""
    return request(`/tasks/my-tasks${query}`)
  },

  // ── Comments ──────────────────────────────────────────────────────
  getComments: (projectUid: string, taskUid: string) =>
    request(`/comments/projects/${projectUid}/tasks/${taskUid}/comments`),

  addComment: (projectUid: string, taskUid: string, data: { content: string }) =>
    request(`/comments/projects/${projectUid}/tasks/${taskUid}/comments`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteComment: (projectUid: string, taskUid: string, commentUid: string) =>
    request(`/comments/projects/${projectUid}/tasks/${taskUid}/comments/${commentUid}`, { method: "DELETE" }),
}
