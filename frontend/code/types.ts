/**
 * Types and interfaces for the In-Browser Python Editor and Live Coding Runner.
 * Aligned with contracts defined in /contracts/openapi.json and /contracts/board_commands.json.
 */

export type CodeActionType = "display" | "type" | "execute" | "explain";

export interface CodeAction {
  code: string;
  language?: string;
  action?: CodeActionType;
  explanation?: string | null;
}

export interface PyodideExecutionResult {
  stdout: string;
  stderr: string;
  result: unknown;
  executionTimeMs: number;
  success: boolean;
  error?: string | null;
  isSimulated?: boolean;
}

export interface LiveCodingStep {
  stepIndex: number;
  chunkTitle?: string;
  codeAction: CodeAction;
  executed?: boolean;
  userEditedCode?: string;
}

export interface PyodideStatus {
  loading: boolean;
  ready: boolean;
  error: string | null;
  version?: string;
  isSimulatedFallback?: boolean;
}
