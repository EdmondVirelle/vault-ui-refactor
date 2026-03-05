import { TaskStatus } from "../domain/task";

export type TaskLogEvent = {
  pid: number;
  task_id: string;
  stream: "stdout" | "stderr" | "system" | string;
  line: string;
};

export type TaskStatusEvent = {
  pid: number;
  task_id: string;
  status: Exclude<TaskStatus, "idle" | "pending">;
  code?: number | null;
  message?: string | null;
};
