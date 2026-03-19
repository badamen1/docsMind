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
  AuthResponse,
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

  sendMessage: (chatId: string, content: string) =>
    apiPost<Message>(`/api/chats/${chatId}/messages/`, { content }),

  delete: (id: string) => apiDelete(`/api/chats/${id}/`),
};

/**
 * SUBSCRIPTION ENDPOINTS
 */
export const subscriptionAPI = {
  get: () => apiGet<Subscription>("/api/subscription/"),
};
