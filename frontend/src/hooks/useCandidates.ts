import { useCallback, useEffect, useState } from "react";
import api from "../api/client";
import type { CandidateDetail, CandidateListItem } from "../types";

export function useCandidates(jobId?: string | number) {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<CandidateListItem[]>(`/jobs/${jobId}/candidates`);
      setCandidates(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { candidates, loading, error, reload };
}

export function useCandidate(candidateId?: string | number) {
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!candidateId) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<CandidateDetail>(`/candidates/${candidateId}`);
      setCandidate(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [candidateId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { candidate, loading, error, reload };
}
