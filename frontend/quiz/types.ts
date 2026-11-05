/**
 * Types and interfaces for the Quiz and Flashcards module (/frontend/quiz).
 * Directly matches /contracts/openapi.json component schemas.
 */

export interface QuizQuestionItem {
  question_id: string;
  concept_tag: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface QuizGenerateRequest {
  topic?: string;
  num_questions?: number;
  weak_concepts?: string[];
  student_id?: string;
}

export interface QuizGenerateResponse {
  quiz_id: string;
  topic: string;
  questions: QuizQuestionItem[];
}

export interface FlashcardItem {
  card_id: string;
  concept_tag: string;
  front: string;
  back: string;
  hint?: string | null;
}

export interface FlashcardsGenerateRequest {
  topic?: string;
  count?: number;
  weak_concepts?: string[];
  student_id?: string;
}

export interface FlashcardsGenerateResponse {
  topic: string;
  cards: FlashcardItem[];
}

export interface QuestionResultFeedback {
  question_id: string;
  concept_tag: string;
  is_correct: boolean;
  selected_index: number;
  correct_index: number;
  explanation: string;
  identified_misconception?: string | null;
}

export interface QuizSubmitRequest {
  quiz_id: string;
  user_id?: string;
  answers: Record<string, number>;
}

export interface QuizSubmitResponse {
  quiz_id: string;
  user_id: string;
  score: number;
  total_questions: number;
  correct_count: number;
  feedback: QuestionResultFeedback[];
}

