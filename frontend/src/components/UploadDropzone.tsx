import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function UploadDropzone({
  onUpload,
  maxMb = 10,
  disabled,
}: {
  onUpload: (files: File[]) => Promise<void> | void;
  maxMb?: number;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (accepted: File[]) => {
      setLocalError(null);
      setBusy(true);
      try {
        await onUpload(accepted);
      } catch (e) {
        setLocalError((e as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    disabled: disabled || busy,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxSize: maxMb * 1024 * 1024,
    multiple: true,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
          isDragActive ? "border-brand-500 bg-brand-50" : "border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 dark:bg-slate-900/50"
        } ${disabled || busy ? "opacity-60" : ""}`}
      >
        <input {...getInputProps()} />
        <div className="text-3xl">📥</div>
        <p className="text-sm font-medium text-ink-800 dark:text-slate-200">
          {busy ? "Uploading and processing…" : "Drag & drop resumes here, or click to browse"}
        </p>
        <p className="text-xs text-ink-500 dark:text-slate-400">PDF or DOCX · up to {maxMb} MB each · multiple files</p>
      </div>
      {localError && <p className="mt-2 text-sm text-rose-600">{localError}</p>}
      {fileRejections.length > 0 && (
        <p className="mt-2 text-sm text-rose-600">
          {fileRejections.length} file(s) rejected (wrong type or too large).
        </p>
      )}
    </div>
  );
}
