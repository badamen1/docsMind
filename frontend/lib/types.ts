/**
 * Tipos compartidos entre frontend y backend
 */

export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  file_name: string;
  file_type: "pdf" | "image" | "docx" | "text";
  file_size: number;
  status: "pending" | "processing" | "completed" | "failed";
  markdown_content: string;
  error_message: string;
  created_at: string;
  updated_at: string;
  user: string;
}

export interface Chat {
  id: string;
  user: string;
  document: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatDetail extends Chat {
  messages: Message[];
}


export interface Message {
  id: string;
  chat: string;
  content: string;
  role: "user" | "assistant";
  created_at: string;
}

export interface Subscription {
  plan: string;
  plan_type: "free" | "pro";
  status: "active" | "cancelled" | "expired";
  price: string;
  max_documents: number;
  max_storage_mb: number;
  is_active: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  access: string;
  refresh: string;
}

export interface ErrorResponse {
  detail?: string;
  error?: string;
  [key: string]: any;
}
