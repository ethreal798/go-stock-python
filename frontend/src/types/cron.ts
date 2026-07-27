export interface CronTask {
  id: number;
  name: string;
  cronExpr: string;
  taskType: string;
  params?: Record<string, unknown>;
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
  status?: "running" | "idle" | "error";
  remark?: string;
}
