import { useCallback, useEffect, useState } from "react";
import api from "../api/client";
import type { Job, JobListItem } from "../types";

export function useJobs() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<JobListItem[]>("/jobs");
      setJobs(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { jobs, loading, error, reload };
}

export function useJob(jobId?: string | number) {
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<Job>(`/jobs/${jobId}`);
      setJob(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { job, loading, error, reload };
}
