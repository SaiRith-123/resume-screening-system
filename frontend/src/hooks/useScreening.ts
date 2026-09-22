import { useCallback, useState } from "react";
import api from "../api/client";
import type { GenAIExplanation, InterviewQuestions, ScreeningResult, UploadResponse } from "../types";

export function useScreening(jobId?: string | number) {
  const [results, setResults] = useState<ScreeningResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<ScreeningResult[]>(`/jobs/${jobId}/results`);
      setResults(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const run = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      await api.post(`/jobs/${jobId}/screen`);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [jobId, load]);

  const upload = useCallback(
    async (files: File[]): Promise<UploadResponse> => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      const { data } = await api.post<UploadResponse>(
        `/jobs/${jobId}/resumes?auto_screen=true&use_llm=true`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return data;
    },
    [jobId]
  );

  return { results, loading, error, load, run, upload };
}

export async function fetchExplanation(candidateId: number): Promise<GenAIExplanation> {
  const { data } = await api.get<GenAIExplanation>(`/candidates/${candidateId}/explanation`);
  return data;
}

export async function fetchInterviewQuestions(
  candidateId: number
): Promise<InterviewQuestions> {
  const { data } = await api.post<InterviewQuestions>(
    `/candidates/${candidateId}/interview-questions`
  );
  return data;
}
