"use client";

import { useCallback, useState, useRef } from "react";

interface UploadZoneProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export function UploadZone({ onUpload, disabled }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) onUpload(file);
    },
    [onUpload, disabled]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file);
      // Reset para permitir subir el mismo archivo
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    [onUpload]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
        transition-all duration-200
        ${
          isDragging
            ? "border-blue-500 bg-blue-500/10"
            : "border-slate-700 hover:border-slate-500 bg-slate-900/50"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp,.tiff,.tif"
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />

      <div className="flex flex-col items-center gap-3">
        <div
          className={`w-14 h-14 rounded-full flex items-center justify-center transition ${
            isDragging ? "bg-blue-500" : "bg-blue-600/20"
          }`}
        >
          <span className="text-2xl">☁️</span>
        </div>
        <div>
          <p className="text-white font-medium">
            Haz clic para subir o arrastra y suelta
          </p>
          <p className="text-slate-400 text-sm mt-1">
            PDF, DOCX, TXT o imágenes (máx. 10MB)
          </p>
        </div>
        <button
          type="button"
          disabled={disabled}
          className="mt-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold
                     rounded-lg transition disabled:opacity-50"
        >
          Seleccionar Archivos
        </button>
      </div>
    </div>
  );
}
