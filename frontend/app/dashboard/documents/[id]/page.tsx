"use client";

/**
 * Página de documento con visor de markdown y panel de chat IA.
 * Layout: documento a la izquierda, chat a la derecha.
 */

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { documentsAPI, chatsAPI, aiAPI } from "@/lib/api-endpoints";
import { Document, ChatDetail, Message, AIProvider } from "@/lib/types";
import { Button } from "@/components/ui/button";

export default function DocumentChatPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [chat, setChat] = useState<ChatDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("gemini");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Cargar documento y crear/obtener chat
  useEffect(() => {
    const init = async () => {
      try {
        const doc = await documentsAPI.get(documentId);
        setDocument(doc);

        // Crear un chat para este documento
        const chatData = await chatsAPI.create(documentId);
        setChat(chatData);
        setMessages(chatData.messages || []);
      } catch {
        // Si falla, intentar cargar solo el documento
        try {
          const doc = await documentsAPI.get(documentId);
          setDocument(doc);
        } catch {
          router.push("/dashboard");
        }
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [documentId, router]);

  // Cargar proveedores de IA disponibles
  useEffect(() => {
    aiAPI.getProviders().then(setProviders).catch(() => {});
  }, []);

  // Scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !chat || sending) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      chat: chat.id,
      role: "user",
      content: input.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);

    try {
      const assistantMessage = await chatsAPI.sendMessage(chat.id, userMessage.content, selectedProvider);
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          chat: chat.id,
          role: "assistant" as const,
          content: "Lo siento, hubo un error al generar la respuesta. Intenta de nuevo.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [input, chat, sending, selectedProvider]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (question: string) => {
    setInput(question);
    setTimeout(() => {
      handleSend();
    }, 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        Documento no encontrado.
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Panel izquierdo — Visor de Documento */}
      <div className="flex-1 flex flex-col border-r border-slate-800 min-w-0">
        {/* Header del documento */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => router.push("/dashboard")}
              className="text-slate-400 hover:text-white transition text-lg"
            >
              ←
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="font-semibold text-white truncate">
                  {document.file_name}
                </h1>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${
                    document.status === "completed"
                      ? "bg-green-500/20 text-green-400"
                      : document.status === "processing"
                      ? "bg-blue-500/20 text-blue-400"
                      : "bg-yellow-500/20 text-yellow-400"
                  }`}
                >
                  {document.status === "completed"
                    ? "Procesado"
                    : document.status === "processing"
                    ? "Procesando"
                    : "Pendiente"}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {document.file_type.toUpperCase()} •{" "}
                {new Date(document.created_at).toLocaleDateString("es")}
              </p>
            </div>
          </div>
        </div>

        {/* Contenido Markdown */}
        <div className="flex-1 overflow-auto p-6">
          {document.markdown_content ? (
            <article className="prose prose-invert prose-sm max-w-none">
              <div
                dangerouslySetInnerHTML={{
                  __html: document.markdown_content
                    .replace(/^### (.*$)/gm, "<h3>$1</h3>")
                    .replace(/^## (.*$)/gm, "<h2>$1</h2>")
                    .replace(/^# (.*$)/gm, "<h1>$1</h1>")
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\*(.*?)\*/g, "<em>$1</em>")
                    .replace(/^- (.*$)/gm, "<li>$1</li>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </article>
          ) : (
            <div className="text-center text-slate-500 py-20">
              <p className="text-4xl mb-4">📄</p>
              <p>El documento aún no ha sido procesado.</p>
            </div>
          )}
        </div>
      </div>

      {/* Panel derecho — Chat IA */}
      <div className="w-96 flex flex-col bg-slate-900">
        {/* Header del chat */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 bg-green-400 rounded-full" />
            <span className="font-semibold text-white">Asistente IA</span>
          </div>
        </div>

        {/* Mensajes */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && !sending && (
            <div className="text-center py-8">
              <p className="text-slate-400 text-sm mb-4">
                He analizado <strong className="text-white">{document.file_name}</strong>.
                Puedo ayudarte a resumir, extraer datos o responder preguntas.
              </p>
              {/* Acciones rápidas */}
              <div className="flex flex-wrap gap-2 justify-center">
                {[
                  "Resumen del documento",
                  "Puntos clave",
                  "¿Qué temas abarca?",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => handleQuickAction(q)}
                    className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-full
                               text-xs text-slate-300 hover:border-blue-500 hover:text-blue-400 transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-md"
                    : "bg-slate-800 text-slate-200 rounded-bl-md"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-blue-400 text-xs">✦</span>
                    <span className="text-xs font-medium text-blue-400">IA</span>
                  </div>
                )}
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </p>
                <p
                  className={`text-[10px] mt-1 ${
                    msg.role === "user" ? "text-blue-200" : "text-slate-500"
                  }`}
                >
                  {new Date(msg.created_at).toLocaleTimeString("es", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-slate-800 rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input + Toolbar */}
        <div className="border-t border-slate-800 p-3">
          <div className="bg-slate-800 rounded-xl overflow-hidden">
            {/* Campo de texto */}
            <div className="flex items-center gap-2 px-3 py-2.5">
              <input
                ref={inputRef}
                type="text"
                placeholder="Haz una pregunta sobre el documento..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sending || document.status !== "completed"}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500
                           focus:outline-none disabled:opacity-50"
              />
              <Button
                size="sm"
                onClick={handleSend}
                disabled={!input.trim() || sending || document.status !== "completed"}
                className="px-3 py-1.5 rounded-lg"
              >
                ➤
              </Button>
            </div>
            {/* Toolbar inferior con selector de modelo */}
            <div className="flex items-center gap-2 px-3 py-1.5 border-t border-slate-700/50">
              <button
                id="ai-provider-toggle"
                onClick={() => {
                  const next = providers.find((p) => p.id !== selectedProvider);
                  if (next) setSelectedProvider(next.id);
                }}
                className="flex items-center gap-1.5 text-xs text-slate-400
                           hover:text-slate-200 transition cursor-pointer rounded px-1.5 py-0.5
                           hover:bg-slate-700/50"
              >
                <span className="text-[10px]">▲</span>
                <span>
                  {providers.find((p) => p.id === selectedProvider)?.name || "Gemini 2.5 Flash"}
                </span>
                {providers.find((p) => p.id === selectedProvider)?.is_premium && (
                  <span className="text-[9px] text-amber-400">⭐</span>
                )}
              </button>
            </div>
          </div>
          <p className="text-[10px] text-slate-600 text-center mt-1.5">
            La IA puede cometer errores. Verifica la información importante.
          </p>
        </div>
      </div>
    </div>
  );
}
