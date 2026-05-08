/**
 * Endpoints de API para cada módulo.
 * Alineados con el backend Django real.
 */

import {
  apiGet,
  apiPost,
  apiDelete,
  apiPostFormData,
} from "./api";
import type {
  User,
  Document,
  Chat,
  ChatDetail,
  Message,
  Subscription,
  SubscriptionDetailResponse,
  AuthResponse,
  AIProvider,
} from "./types";

/**
 * AUTH ENDPOINTS
 */
export const authAPI = {
  register: (data: {
    email: string;
    username: string;
    password: string;
    password_confirm: string;
  }) => apiPost<AuthResponse>("/api/register/", data),

  login: (email: string, password: string) =>
    apiPost<AuthResponse>("/api/login/", { email, password }),

  logout: () => apiPost<{ detail: string }>("/api/logout/"),

  getMe: () => apiGet<User>("/api/me/"),
};

/**
 * DOCUMENTS ENDPOINTS
 */
export const documentsAPI = {
  list: () => apiGet<Document[]>("/api/documents/"),

  get: (id: string) => apiGet<Document>(`/api/documents/${id}/`),

  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiPostFormData<Document>("/api/documents/upload/", formData);
  },

  delete: (id: string) => apiDelete(`/api/documents/${id}/delete/`),
};

/**
 * CHATS ENDPOINTS
 */
export const chatsAPI = {
  list: () => apiGet<Chat[]>("/api/chats/"),

  get: (id: string) => apiGet<ChatDetail>(`/api/chats/${id}/`),

  create: (documentId: string) =>
    apiPost<ChatDetail>("/api/chats/create/", { document_id: documentId }),

  sendMessage: (chatId: string, content: string, provider: string = "gemini") =>
    apiPost<Message>(`/api/chats/${chatId}/messages/`, { content, provider }),

  delete: (id: string) => apiDelete(`/api/chats/${id}/`),
};

/**
 * SUBSCRIPTION ENDPOINTS
 */
export const subscriptionAPI = {
  setupIntent: () =>
    apiPost<{ client_secret: string }>("/api/subscription/setup-intent/"),

  detail: () =>
    apiGet<SubscriptionDetailResponse>("/api/subscription/detail/"),

  subscribe: (product_id: string, payment_method_id: string) =>
    apiPost<{ subscription_id: string; status: string; product: object }>(
      "/api/subscription/subscribe/",
      { product_id, payment_method_id }
    ),

  cancel: (immediate = false) =>
    apiPost<{ status: string; message: string }>(
      "/api/subscription/cancel/",
      { immediate }
    ),
};

/**
 * AI PROVIDERS ENDPOINTS
 */
export const aiAPI = {
  getProviders: () => apiGet<AIProvider[]>("/api/ai/providers/"),
};
