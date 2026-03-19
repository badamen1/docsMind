"use client";

/**
 * Lista de chats recientes del usuario.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { chatsAPI } from "@/lib/api-endpoints";
import { Chat } from "@/lib/types";

export default function ChatsPage() {
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    chatsAPI
      .list()
      .then(setChats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (chat: Chat) => {
    if (!confirm(`¿Eliminar "${chat.title}"?`)) return;
    try {
      await chatsAPI.delete(chat.id);
      setChats((prev) => prev.filter((c) => c.id !== chat.id));
    } catch {
      // Silenciar
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Chats Recientes</h1>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
        </div>
      ) : chats.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-4xl mb-4">💬</p>
          <p className="text-slate-400 text-lg">
            No tienes chats aún. Sube un documento y empieza a chatear.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className="bg-slate-800/50 border border-slate-700 rounded-xl p-4
                         hover:border-slate-600 transition cursor-pointer group"
              onClick={() => router.push(`/dashboard/documents/${chat.document}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <span className="text-lg">💬</span>
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-white truncate">
                      {chat.title}
                    </h3>
                    <p className="text-xs text-slate-500">
                      {new Date(chat.updated_at).toLocaleDateString("es", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(chat);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-slate-500
                             hover:text-red-400 transition text-sm px-2"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
