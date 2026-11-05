/**
 * TypeScript Contracts for Classroom Frontend (/frontend/classroom)
 * Aligned with /contracts/board_commands.json and /contracts/openapi.json
 */

export interface TextCommand {
  type: "text";
  id: string;
  content: string;
  x: number;
  y: number;
  size?: number;
  color?: string;
}

export interface BoxCommand {
  type: "box";
  id: string;
  label?: string | null;
  x: number;
  y: number;
  width?: number;
  height?: number;
  color?: string;
  fill?: string;
}

export interface ArrowCommand {
  type: "arrow";
  id: string;
  from_id?: string | null;
  to_id?: string | null;
  start_x?: number | null;
  start_y?: number | null;
  end_x?: number | null;
  end_y?: number | null;
  label?: string | null;
  color?: string;
}

export interface EquationCommand {
  type: "equation";
  id: string;
  latex: string;
  x: number;
  y: number;
  label?: string | null;
}

export interface MermaidCommand {
  type: "mermaid";
  id: string;
  chart: string;
  x?: number;
  y?: number;
  title?: string | null;
}

export interface ClearCommand {
  type: "clear";
  id?: string;
}

export type BoardCommand =
  | TextCommand
  | BoxCommand
  | ArrowCommand
  | EquationCommand
  | MermaidCommand
  | ClearCommand;

export interface CodeAction {
  code: string;
  language?: string;
  action?: "display" | "type" | "execute" | "explain";
  explanation?: string | null;
}

export interface CheckQuestion {
  question_id: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  concept_tag: string;
}

export interface ToolCallRecord {
  tool_name: string;
  parameters?: Record<string, any>;
  result?: any;
}

export interface LessonStep {
  step_id: string;
  step_index: number;
  total_steps?: number;
  concept: string;
  narration: string;
  board_commands: BoardCommand[];
  code_action?: CodeAction | null;
  check_question?: CheckQuestion | null;
  agent_thoughts?: string | null;
  detected_misconception?: string | null;
  remediation?: string | null;
  provider_metadata?: Record<string, any> | null;
  tool_calls?: ToolCallRecord[];
  is_final_step?: boolean;
}

export interface LessonStepRequest {
  concept?: string;
  student_id?: string;
  step_index?: number;
  last_student_response?: string | null;
  student_misconceptions?: string[];
  feedback?: string | null;
}

export interface CheckAnswerRequest {
  question_id: string;
  selected_index: number;
  concept?: string;
  student_id?: string;
}

export interface CheckAnswerResponse {
  is_correct: boolean;
  correct_index: number;
  explanation: string;
  detected_misconception?: string | null;
  remediation?: string | null;
  updated_mastery_score: number;
  suggested_board_commands?: BoardCommand[];
}

export interface ChatMessageRequest {
  student_id?: string;
  concept?: string;
  message: string;
  current_step_index?: number;
}

export interface ChatMessageResponse {
  reply: string;
  suggested_board_commands?: BoardCommand[];
  agent_thoughts?: string | null;
}

export interface ChatItem {
  id: string;
  sender: "student" | "teacher";
  text: string;
  timestamp: string;
  agent_thoughts?: string | null;
}

export interface VoiceSettings {
  enabled: boolean;
  rate: number;
  pitch: number;
  volume: number;
  voiceName?: string;
}
