"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, CheckCircle2, AlertCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

export default function DocumentsPage() {
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === "application/pdf" || f.type.startsWith("image/")
    );
    setFiles((prev) => [...prev, ...dropped]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []).filter(
      (f) => f.type === "application/pdf" || f.type.startsWith("image/")
    );
    setFiles((prev) => [...prev, ...selected]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    setUploading(true);
    // Simulate upload — in production, this calls the API
    await new Promise((r) => setTimeout(r, 2000));
    setFiles([]);
    setUploading(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-heading font-bold">Documents</h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload Aadhaar, PAN, or certificates for AI analysis
        </p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200",
          dragOver
            ? "border-saffron-500 bg-saffron-500/5"
            : "border-border hover:border-saffron-500/30 hover:bg-secondary/30"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center mx-auto mb-4">
          <Upload className="w-6 h-6 text-saffron-500" />
        </div>
        <p className="text-base font-medium mb-1">Drop your documents here</p>
        <p className="text-sm text-slate-400">
          PDF, JPEG, or PNG — Max 10MB each
        </p>
      </div>

      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <h3 className="text-sm font-medium">{files.length} file{files.length > 1 ? "s" : ""} selected</h3>
          {files.map((file, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-xl border border-border bg-card"
            >
              <FileText className="w-5 h-5 text-saffron-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-slate-500">
                  {(file.size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
              <button
                onClick={() => removeFile(i)}
                className="p-1 rounded-lg text-slate-400 hover:text-destructive"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          <Button
            variant="saffron"
            onClick={uploadFiles}
            disabled={uploading}
            className="w-full gap-2"
          >
            {uploading ? (
              <>Analyzing...</>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload & Analyze
              </>
            )}
          </Button>
        </motion.div>
      )}

      {!uploading && files.length === 0 && (
        <div className="text-center py-12">
          <div className="w-12 h-12 rounded-xl bg-secondary/50 flex items-center justify-center mx-auto mb-3">
            <FileText className="w-6 h-6 text-slate-400" />
          </div>
          <p className="text-sm text-slate-400">No documents uploaded yet</p>
          <p className="text-xs text-slate-600 mt-1">
            Uploaded documents will appear here for AI analysis
          </p>
        </div>
      )}
    </div>
  );
}
