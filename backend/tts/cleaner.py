import re


def strip_markdown_and_latex(text: str) -> str:
    """
    Strips markdown formatting, LaTeX formulas, and code blocks
    to produce clean, natural spoken text for TTS synthesis.
    """
    if not text:
        return ""

    # 1. Remove fenced code blocks (```...```)
    text = re.sub(r"```[\s\S]*?```", "", text)

    # 2. Remove inline code (`...`)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 3. Clean or remove LaTeX math equations
    # Display equations: $$...$$ or \[...\]
    text = re.sub(r"\$\$[\s\S]*?\$\$", "", text)
    text = re.sub(r"\\\[[\s\S]*?\\\]", "", text)

    # Inline equations: $...$ or \(...\)
    def clean_inline_latex(match: re.Match) -> str:
        eq = match.group(1).strip()
        # Clean common LaTeX commands for audio readability
        eq = re.sub(r"\\mathcal\{([^}]+)\}", r"\1", eq)
        eq = re.sub(r"\\text\{([^}]+)\}", r"\1", eq)
        eq = re.sub(r"\\mathbf\{([^}]+)\}", r"\1", eq)
        eq = re.sub(r"\\log_2", "log base 2", eq)
        eq = re.sub(r"\\log", "log", eq)
        eq = re.sub(r"\\ll", "is much less than", eq)
        eq = re.sub(r"\\le", "<=", eq)
        eq = re.sub(r"\\ge", ">=", eq)
        eq = re.sub(r"\\neq", "!=", eq)
        eq = re.sub(r"\\times", "times", eq)
        eq = re.sub(r"\^\{?([0-9a-zA-Z]+)\}?", r" to the power of \1", eq)
        eq = re.sub(r"\_\{?([0-9a-zA-Z]+)\}?", r" \1", eq)
        # Remove remaining backslashes and braces
        eq = re.sub(r"\\[a-zA-Z]+", "", eq)
        eq = re.sub(r"[{}]", "", eq)
        return eq.strip()

    text = re.sub(r"\$([^$]+)\$", clean_inline_latex, text)
    text = re.sub(r"\\\(([^)]+)\\\)", clean_inline_latex, text)

    # 4. Remove Markdown images and links: ![alt](url) -> "" and [text](url) -> text
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    # 5. Remove headers: #, ##, ###, etc.
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # 6. Remove bold/italics: **text**, *text*, __text__, _text_
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

    # 7. Remove list markers, blockquotes, horizontal rules
    text = re.sub(r"^[\*\-\+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # 8. Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # 9. Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
