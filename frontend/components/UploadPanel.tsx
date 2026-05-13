interface UploadPanelProps {
  file: File | null;
  isLoading: boolean;
  error: string | null;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
}

export default function UploadPanel({
  file,
  isLoading,
  error,
  onFileChange,
  onAnalyze,
}: UploadPanelProps) {
  return (
    <section className="upload-panel" aria-label="Upload PDF for analysis">
      <label className="file-input">
        <span>SPA PDF</span>
        <input
          type="file"
          accept="application/pdf"
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
        />
      </label>

      <button className="primary-button" type="button" disabled={!file || isLoading} onClick={onAnalyze}>
        {isLoading ? "Running..." : "Run analysis"}
      </button>

      {error && <p className="error-text">{error}</p>}
    </section>
  );
}
