import { useState } from "react";
import { uploadArtifacts } from "../lib/api";

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(sessionId: string, files: File[], artifactTypes: string[]) {
    setUploading(true);
    setError(null);
    try {
      return await uploadArtifacts(sessionId, files, artifactTypes);
    } catch (e: any) {
      setError(e?.message ?? "Upload failed");
      throw e;
    } finally {
      setUploading(false);
    }
  }

  return { upload, uploading, error };
}

