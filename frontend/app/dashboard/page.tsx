"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { documentsAPI } from "@/lib/api-endpoints";
import { Document } from "@/lib/types";
import { UploadZone } from "@/components/dashboard/UploadZone";
import { DocumentCard } from "@/components/dashboard/DocumentCard";

type StatusFilter = "all" | "completed" | "processing" | "pending" | "failed";
type ViewMode = "grid" | "list";

export default function DashboardPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const fetchDocuments = useCallback(async () => {
    try {
      const docs = await documentsAPI.list();
      setDocuments(docs);
    } catch {
      // Silenciar error si no hay docs
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await documentsAPI.upload(file);
      await fetchDocuments();
    } catch (err) {
      console.error("Error al subir:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleChat = (doc: Document) => {
    router.push(`/dashboard/documents/${doc.id}`);
  };

  const handleDelete = async (doc: Document) => {
    if (!confirm(`¿Eliminar "${doc.file_name}"?`)) return;
    try {
      await documentsAPI.delete(doc.id);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err) {
      console.error("Error al eliminar:", err);
    }
  };

  // Filtrar documentos
  const filtered = documents.filter((doc) => {
    const matchSearch = doc.file_name
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchStatus =
      statusFilter === "all" || doc.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Biblioteca</h1>
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">
              
            </span>
            <input
              type="text"
              placeholder="Buscar documentos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm
                         text-white placeholder-slate-500 focus:outline-none focus:border-blue-500
                         w-64 transition"
            />
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="mb-8">
        <UploadZone onUpload={handleUpload} disabled={uploading} />
        {uploading && (
          <p className="text-center text-blue-400 text-sm mt-2 animate-pulse">
            Subiendo archivo...
          </p>
        )}
      </div>

      {/* Documents Section */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Tus Documentos</h2>
          <span className="bg-slate-700 text-slate-300 text-xs font-medium px-2.5 py-0.5 rounded-full">
            {filtered.length}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="bg-slate-800 border border-slate-700 text-sm text-slate-300
                       rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500"
          >
            <option value="all">Todos</option>
            <option value="completed">Listos</option>
            <option value="processing">Procesando</option>
            <option value="pending">Pendientes</option>
            <option value="failed">Con Error</option>
          </select>

          {/* View Toggle */}
          <div className="flex bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode("grid")}
              className={`px-3 py-2 text-sm transition ${
                viewMode === "grid"
                  ? "bg-slate-700 text-white"
                  : "text-slate-500 hover:text-white"
              }`}
              title="Vista en cuadrícula"
            >
              ▦
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`px-3 py-2 text-sm transition ${
                viewMode === "list"
                  ? "bg-slate-700 text-white"
                  : "text-slate-500 hover:text-white"
              }`}
              title="Vista en lista"
            >
              ☰
            </button>
          </div>
        </div>
      </div>

      {/* Documents Grid/List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-4xl mb-4">📂</p>
          <p className="text-slate-400 text-lg">
            {documents.length === 0
              ? "No tienes documentos aún. ¡Sube el primero!"
              : "No se encontraron documentos con ese filtro."}
          </p>
        </div>
      ) : (
        <div
          className={
            viewMode === "grid"
              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
              : "flex flex-col gap-3"
          }
        >
          {filtered.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onChat={handleChat}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
