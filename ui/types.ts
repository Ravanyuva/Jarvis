export interface Message {
  id: string;
  role: 'user' | 'model' | 'system';
  text: string;
  timestamp: Date;
  isCommand?: boolean;
}

export interface SystemMetric {
  time: string;
  value: number;
}

export enum AppStatus {
  IDLE = 'IDLE',
  LISTENING = 'LISTENING',
  PROCESSING = 'PROCESSING',
  SPEAKING = 'SPEAKING',
  EXECUTING = 'EXECUTING'
}

export interface CommandExecution {
  command: string;
  target: string;
  status: 'success' | 'pending' | 'failed';
}
