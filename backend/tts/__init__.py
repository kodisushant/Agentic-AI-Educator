"""
ElevenLabs Text-to-Speech (TTS) Service Package.
Provides cached audio synthesis with fallback to browser speech synthesis.
"""

from backend.tts.cleaner import strip_markdown_and_latex

__all__ = ["strip_markdown_and_latex"]
