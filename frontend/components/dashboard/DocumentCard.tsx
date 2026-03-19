"use client";

import { Document } from "@/lib/types";

interface DocumentCardProps {
  document: Document;
  onChat: (doc: Document) => void;
  onDelete: (doc: Document) => void;
}

const FILE_ICONS: Record<string, { icon: string; color: string }> = {
  pdf: { icon: "📄", color: "bg-red-500/20 border-red-500/30" },
  image: { icon: "🖼️", color: "bg-purple-500/20 border-purple-500/30" },
  docx: { icon: "📝", color: "bg-blue-500/20 border-blue-500/30" },
  text: { icon: "📃", color: "bg-green-500/20 border-green-500/30" },
};

const STATUS_BADGES: Record<
  string,
  { label: string; color: string; dot: string }
> = {
  completed: {
    label: "Listo",
    color: "text-green-400",
    dot: "bg-green-400",
  },
  processing: {
    label: "Procesando...",
    color: "text-blue-400",
    dot: "bg-blue-400 animate-pulse",
  },
  pending: {
    label: "Pendiente",
    color: "text-yellow-400",
    dot: "bg-yellow-400",
  },
  failed: {
    label: "Error",
    color: "text-red-400",
    dot: "bg-red-400",
  },
};

function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return "0 KB";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Ahora";
  if (diffMins < 60) return `Hace ${diffMins}m`;
  if (diffHours < 24) return `Hace ${diffHours}h`;
  if (diffDays < 7) return `Hace ${diffDays}d`;
  return date.toLocaleDateString("es");
}

export function DocumentCard({ document: doc, onChat, onDelete }: DocumentCardProps) {
  const fileInfo = FILE_ICONS[doc.file_type] || FILE_ICONS.text;
  const status = STATUS_BADGES[doc.status] || STATUS_BADGES.pending;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 hover:border-slate-600 transition group">
      {/* Header: icon + delete */}
      <div className="flex items-start justify-between mb-3">
        <div
          className={`w-10 h-10 rounded-lg border flex items-center justify-center ${fileInfo.color}`}
        >
          <span className="text-lg">{fileInfo.icon}</span>
        </div>
        <button
          onClick={() => onDelete(doc)}
          className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition text-sm"
          title="Eliminar"
        >
          ✕
        </button>
      </div>

      {/* Name + meta */}
      <h3 className="text-sm font-semibold text-white truncate mb-1" title={doc.file_name}>
        {doc.file_name}
      </h3>
      <p className="text-xs text-slate-500 mb-3">
        {formatFileSize(doc.file_size || 0)} • {doc.file_type.toUpperCase()}
      </p>

      {/* Status + time */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${status.dot}`} />
          <span className={`text-xs font-medium ${status.color}`}>
            {status.label}
          </span>
        </div>
        <span className="text-xs text-slate-500">
          {formatTimeAgo(doc.created_at)}
        </span>
      </div>

      {/* Actions */}
      {doc.status === "completed" && (
        <button
          onClick={() => onChat(doc)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2
                     bg-slate-700/50 hover:bg-slate-700 rounded-lg text-sm text-slate-300
                     hover:text-white transition"
        >
          💬 Chatear con Doc
        </button>
      )}

      {doc.status === "failed" && doc.error_message && (
        <p className="text-xs text-red-400 mt-1 line-clamp-2">
          {doc.error_message}
        </p>
      )}
    </div>
  );
}
