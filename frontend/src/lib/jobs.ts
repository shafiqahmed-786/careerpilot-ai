import { api, type Job } from "@/lib/api";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Polls a background job until it completes or fails, or until the timeout passes. */
export async function waitForJob(
  jobId: string,
  options: { intervalMs?: number; timeoutMs?: number; onUpdate?: (job: Job) => void } = {},
): Promise<Job> {
  const interval = options.intervalMs ?? 1500;
  const deadline = Date.now() + (options.timeoutMs ?? 180_000);
  for (;;) {
    const job = await api<Job>(`/api/v1/jobs/${jobId}`);
    options.onUpdate?.(job);
    if (job.status === "completed" || job.status === "failed") return job;
    if (Date.now() > deadline) {
      throw new Error("The job is taking longer than expected. Make sure the RQ worker is running (python -m app.worker).");
    }
    await sleep(interval);
  }
}
