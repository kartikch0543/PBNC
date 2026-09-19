import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.question import QuestionType


class RawQuestion:
    """Internal representation of a question extracted before persistence."""
    def __init__(
        self,
        question_number: Optional[str],
        question_text: str,
        options: List[Dict[str, Any]],
        question_type: QuestionType,
        source_pages: List[int],
        detected_answer: Optional[str] = None,
        has_diagram: bool = False,
        warnings: Optional[List[str]] = None,
    ):
        self.question_number = question_number
        self.question_text = question_text
        self.options = options
        self.question_type = question_type
        self.source_pages = source_pages
        self.detected_answer = detected_answer
        self.has_diagram = has_diagram
        self.warnings = warnings or []


class QuestionExtractor:
    """
    Deterministic rule-based Question & Option Boundary Segmenter.
    Works independently of external AI, supporting multi-page spanning,
    diverse numbering styles, and unnumbered questions.
    """

    # Question start pattern:
    # 1. "Q1.", "Q. 1", "Question 1:", "1.", "1)", "(1)"
    QUESTION_ANCHOR_REGEX = re.compile(
        r"^(?:(?:Q(?:uestion)?\.?\s*(\d+[a-zA-Z]?))|(?:\((\d+[a-zA-Z]?)\))|(?:(\d+[a-zA-Z]?)[.)]))\s*[:.-]?\s*(.*)",
        re.IGNORECASE,
    )

    # Option patterns:
    # (A), (a), A., A), (i), (ii)
    OPTION_LINE_REGEX = re.compile(
        r"^(?:(?:\(([a-dA-D]|(?:[i-v]{1,4}))\))|(?:([a-dA-D]|(?:[i-v]{1,4}))[.)]))\s+(.*)",
    )

    # Answer Key header pattern
    ANSWER_KEY_HEADER_REGEX = re.compile(
        r"(?:answer\s*key|solutions?|correct\s*answers?)\s*[:.-]?",
        re.IGNORECASE,
    )

    # Inline answer pattern: "Ans: A", "Answer: (B)", "Correct Answer: Option C"
    INLINE_ANSWER_REGEX = re.compile(
        r"(?:ans(?:wer)?|correct\s*option)\s*[:.-]?\s*(?:\(?([a-dA-D0-9]+)\)?)",
        re.IGNORECASE,
    )

    @classmethod
    def extract_from_pages(cls, pages_data: List[Tuple[int, str]]) -> Tuple[List[RawQuestion], Dict[str, str]]:
        """
        Parses questions and standalone answer keys across ordered document pages.
        Handles questions spanning across page breaks.
        """
        extracted_questions: List[RawQuestion] = []
        answer_key_dict: Dict[str, str] = {}

        current_q_number: Optional[str] = None
        current_text_lines: List[str] = []
        current_options: List[Dict[str, Any]] = []
        current_pages: List[int] = []
        current_inline_ans: Optional[str] = None
        in_answer_key_section = False

        for page_num, page_text in pages_data:
            lines = [line.strip() for line in page_text.splitlines() if line.strip()]

            for line in lines:
                # 1. Check if we entered an Answer Key block at document tail/header
                if cls.ANSWER_KEY_HEADER_REGEX.match(line):
                    in_answer_key_section = True
                    # Flush any open question before reading answer key
                    if current_text_lines or current_options:
                        cls._flush_question(
                            extracted_questions,
                            current_q_number,
                            current_text_lines,
                            current_options,
                            current_pages,
                            current_inline_ans,
                        )
                        current_q_number = None
                        current_text_lines = []
                        current_options = []
                        current_pages = []
                        current_inline_ans = None
                    continue

                if in_answer_key_section:
                    # Parse answer key pairs, e.g. "1. A", "2: (B)", "3 - C"
                    pair_matches = re.findall(r"(?:Q\.?)?(\d+)\s*[:.-]?\s*\(?([A-Da-d])\)?", line)
                    for q_num, ans in pair_matches:
                        answer_key_dict[q_num] = ans.upper()
                    continue

                # 2. Check for question anchor
                q_match = cls.QUESTION_ANCHOR_REGEX.match(line)
                if q_match:
                    # Save previous question if exists
                    if current_text_lines or current_options:
                        cls._flush_question(
                            extracted_questions,
                            current_q_number,
                            current_text_lines,
                            current_options,
                            current_pages,
                            current_inline_ans,
                        )
                        current_text_lines = []
                        current_options = []
                        current_pages = []
                        current_inline_ans = None

                    # Extract question number from regex capture groups
                    num = q_match.group(1) or q_match.group(2) or q_match.group(3)
                    remainder_text = q_match.group(4)

                    current_q_number = num
                    current_pages = [page_num]
                    if remainder_text:
                        current_text_lines.append(remainder_text)
                    continue

                # 3. Check for option anchor
                opt_match = cls.OPTION_LINE_REGEX.match(line)
                if opt_match and (current_text_lines or current_q_number is not None):
                    key = (opt_match.group(1) or opt_match.group(2)).upper()
                    opt_text = opt_match.group(3)
                    current_options.append({"key": key, "text": opt_text})
                    if page_num not in current_pages:
                        current_pages.append(page_num)
                    continue

                # 4. Check for inline answer label
                ans_match = cls.INLINE_ANSWER_REGEX.search(line)
                if ans_match and (current_text_lines or current_options):
                    current_inline_ans = ans_match.group(1).upper()
                    continue

                # 5. Normal text continuation (or unnumbered question)
                if current_text_lines or current_q_number is not None:
                    # Question continuation (potentially across page break)
                    current_text_lines.append(line)
                    if page_num not in current_pages:
                        current_pages.append(page_num)
                else:
                    # Header/metadata filters
                    is_header = bool(re.search(r"\b(examination|total marks|minutes|instructions|paper code|department|university|school|midterm|test|quiz)\b", line, re.IGNORECASE))
                    is_divider = line.startswith("---") or line.startswith("===")
                    
                    if not is_header and not is_divider:
                        # Check if line looks like a legitimate question stem
                        starts_with_question_verb = bool(re.match(r"^(?:what|which|why|how|who|where|when|explain|describe|calculate|determine|find|state|define|compare|discuss|prove|show|identify|evaluate)\b", line, re.IGNORECASE))
                        if line.endswith("?") or (starts_with_question_verb and len(line) > 20):
                            current_q_number = None  # Explicitly None (never fake a number)
                            current_text_lines.append(line)
                            current_pages = [page_num]

        # Flush final remaining question
        if current_text_lines or current_options:
            cls._flush_question(
                extracted_questions,
                current_q_number,
                current_text_lines,
                current_options,
                current_pages,
                current_inline_ans,
            )

        return extracted_questions, answer_key_dict

    @classmethod
    def _flush_question(
        cls,
        target_list: List[RawQuestion],
        q_num: Optional[str],
        text_lines: List[str],
        options: List[Dict[str, Any]],
        pages: List[int],
        inline_ans: Optional[str],
    ) -> None:
        """Assembles a RawQuestion object and appends to the extracted list."""
        full_text = " ".join(text_lines).strip()
        if not full_text and not options:
            return

        warnings: List[str] = []

        if q_num is None:
            warnings.append("MISSING_QUESTION_NUMBER")

        if len(pages) > 1:
            warnings.append("SPLIT_PAGE_CONTINUATION")

        # Classify question type
        if len(options) >= 2:
            q_type = QuestionType.MULTIPLE_CHOICE
        elif re.search(r"\b(true\s+or\s+false|true/false)\b", full_text, re.IGNORECASE):
            q_type = QuestionType.TRUE_FALSE
        elif len(full_text) > 300:
            q_type = QuestionType.ESSAY
        else:
            q_type = QuestionType.SHORT_ANSWER

        target_list.append(
            RawQuestion(
                question_number=q_num,
                question_text=full_text,
                options=options,
                question_type=q_type,
                source_pages=pages,
                detected_answer=inline_ans,
                warnings=warnings,
            )
        )


question_extractor = QuestionExtractor()
