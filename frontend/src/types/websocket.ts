export interface WSMessage {
  channel: string;
  type: string;
  data: unknown;
  timestamp: number;
}
