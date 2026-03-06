"""
Questioning Step - Whole-document comprehension testing.

This module implements Step 5 of the document polishing pipeline:
- Load human-authored question sets from YAML
- Query models with scenario-based questions
- Evaluate answers with an LLM-as-Judge
- Score comprehension and map issues to ambiguity-compatible objects
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from ambiguity_detector import Ambiguity, Interpretation, Severity
from model_interface import ModelManager
from session_init_step import SessionInitStep


class QuestionSetValidationError(ValueError):
    """Raised when question set YAML fails validation."""


@dataclass
class QuestionExpected:
    """Expected answer structure for a question."""

    key_points: List[str]
    anti_points: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class WholeDocumentQuestion:
    """Single whole-document question."""

    id: str
    question: str
    category: str
    difficulty: str
    assertions: Optional[List[str]] = None
    expected: QuestionExpected = field(default_factory=lambda: QuestionExpected(key_points=[]))


@dataclass
class QuestionSet:
    """Parsed question-set YAML payload."""

    version: str
    document: str
    questions: List[WholeDocumentQuestion] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    bulky_source: Optional[str] = None
    created: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None


@dataclass
class QuestionEvaluation:
    """Evaluation for one model answer on one question."""

    question_id: str
    model_name: str
    answer_text: str
    verdict: str
    matched_key_points: int
    total_key_points: int
    anti_points_present: List[str] = field(default_factory=list)
    key_point_coverage: Dict[str, bool] = field(default_factory=dict)
    anti_point_presence: Dict[str, bool] = field(default_factory=dict)
    is_evasive: bool = False
    reasoning: str = ""

    def score(self) -> float:
        """Calculate score using the Step 5 scoring formula."""
        return calculate_final_score(
            matched_key_points=self.matched_key_points,
            total_key_points=self.total_key_points,
            has_anti_points=bool(self.anti_points_present),
        )


@dataclass
class QuestioningResult:
    """Result of Step 5 questioning."""

    question_set: QuestionSet
    model_names: List[str] = field(default_factory=list)
    judge_model: str = "claude"
    responses: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    evaluations: Dict[str, Dict[str, QuestionEvaluation]] = field(default_factory=dict)
    question_scores: Dict[str, float] = field(default_factory=dict)
    document_score: float = 0.0
    consensus: Dict[str, str] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)

    def save(self, workspace_path: str):
        """Save Step 5 artifacts to question_responses.json and question_evaluations.json."""
        workspace = Path(workspace_path)
        workspace.mkdir(parents=True, exist_ok=True)

        responses_file = workspace / "question_responses.json"
        with open(responses_file, "w", encoding="utf-8") as f:
            json.dump(self.responses, f, indent=2, ensure_ascii=False)

        evaluations_file = workspace / "question_evaluations.json"
        evaluations_payload = {
            "question_set": {
                "version": self.question_set.version,
                "document": self.question_set.document,
                "metadata": self.question_set.metadata,
                "bulky_source": self.question_set.bulky_source,
                "created": self.question_set.created,
                "author": self.question_set.author,
                "description": self.question_set.description,
                "questions": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "category": q.category,
                        "difficulty": q.difficulty,
                        "assertions": q.assertions,
                        "expected": {
                            "key_points": q.expected.key_points,
                            "anti_points": q.expected.anti_points,
                            "notes": q.expected.notes,
                        },
                    }
                    for q in self.question_set.questions
                ],
            },
            "model_names": self.model_names,
            "judge_model": self.judge_model,
            "question_scores": self.question_scores,
            "document_score": self.document_score,
            "consensus": self.consensus,
            "issues": self.issues,
            "evaluations": {
                qid: {
                    model: {
                        "question_id": ev.question_id,
                        "model_name": ev.model_name,
                        "answer_text": ev.answer_text,
                        "verdict": ev.verdict,
                        "matched_key_points": ev.matched_key_points,
                        "total_key_points": ev.total_key_points,
                        "anti_points_present": ev.anti_points_present,
                        "key_point_coverage": ev.key_point_coverage,
                        "anti_point_presence": ev.anti_point_presence,
                        "is_evasive": ev.is_evasive,
                        "reasoning": ev.reasoning,
                        "score": ev.score(),
                    }
                    for model, ev in model_evals.items()
                }
                for qid, model_evals in self.evaluations.items()
            },
        }
        with open(evaluations_file, "w", encoding="utf-8") as f:
            json.dump(evaluations_payload, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, workspace_path: str) -> "QuestioningResult":
        """Load Step 5 artifacts from workspace."""
        workspace = Path(workspace_path)
        responses_file = workspace / "question_responses.json"
        evaluations_file = workspace / "question_evaluations.json"

        if not responses_file.exists():
            raise FileNotFoundError(f"Question responses not found: {responses_file}")
        if not evaluations_file.exists():
            raise FileNotFoundError(f"Question evaluations not found: {evaluations_file}")

        with open(responses_file, "r", encoding="utf-8") as f:
            responses = json.load(f)

        with open(evaluations_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        question_set_payload = payload["question_set"]
        question_set = load_question_set_from_dict(question_set_payload)

        evaluations: Dict[str, Dict[str, QuestionEvaluation]] = {}
        for qid, model_evals in payload.get("evaluations", {}).items():
            evaluations[qid] = {}
            for model, ev in model_evals.items():
                evaluations[qid][model] = QuestionEvaluation(
                    question_id=ev["question_id"],
                    model_name=ev["model_name"],
                    answer_text=ev.get("answer_text", ""),
                    verdict=ev["verdict"],
                    matched_key_points=ev["matched_key_points"],
                    total_key_points=ev["total_key_points"],
                    anti_points_present=ev.get("anti_points_present", []),
                    key_point_coverage=ev.get("key_point_coverage", {}),
                    anti_point_presence=ev.get("anti_point_presence", {}),
                    is_evasive=ev.get("is_evasive", False),
                    reasoning=ev.get("reasoning", ""),
                )

        return cls(
            question_set=question_set,
            model_names=payload.get("model_names", []),
            judge_model=payload.get("judge_model", "claude"),
            responses=responses,
            evaluations=evaluations,
            question_scores=payload.get("question_scores", {}),
            document_score=payload.get("document_score", 0.0),
            consensus=payload.get("consensus", {}),
            issues=payload.get("issues", []),
        )

    def to_ambiguities(self) -> List[Ambiguity]:
        """Convert detected question issues to ambiguity-compatible objects."""
        ambiguities: List[Ambiguity] = []
        question_map = {q.id: q for q in self.question_set.questions}

        for issue in self.issues:
            question = question_map.get(issue["question_id"])
            if not question:
                continue

            severity = map_issue_to_severity(issue["issue_type"])
            model_name = issue["model_name"]
            answer_summary = issue.get("answer_summary", "")

            ambiguities.append(
                Ambiguity(
                    section_id=f"question_{question.id}_{model_name}",
                    section_header=f"Question {question.id}",
                    section_content=question.question,
                    severity=severity,
                    interpretations={
                        model_name: Interpretation(
                            model_name=model_name,
                            raw_response=answer_summary,
                            interpretation=answer_summary,
                            ambiguities=[issue["issue_type"]],
                        )
                    },
                    comparison_details={
                        "source": "question_testing",
                        "question_id": question.id,
                        "model": model_name,
                        "issue_type": issue["issue_type"],
                        "verdict": issue["verdict"],
                        "expected_key_points": question.expected.key_points,
                        "problematic_answer": issue.get("answer_summary", ""),
                        "details": issue.get("issue", ""),
                    },
                )
            )

        return ambiguities


ISSUE_SEVERITY_MAP = {
    "conflict not detected": Severity.CRITICAL,
    "false premise accepted": Severity.HIGH,
    "incorrect answer": Severity.HIGH,
    "partially correct": Severity.MEDIUM,
    "adversarial failure": Severity.MEDIUM,
}


def map_issue_to_severity(issue_type: str) -> Severity:
    """Map question issue type to ambiguity severity."""
    return ISSUE_SEVERITY_MAP.get(issue_type.lower(), Severity.MEDIUM)


def calculate_question_score(matched_key_points: int, total_key_points: int, has_anti_points: bool) -> float:
    """Calculate per-answer score (before question-level aggregation)."""
    if total_key_points <= 0:
        return 0.0

    score = matched_key_points / total_key_points
    penalty = 1.0 if has_anti_points else 0.0
    return max(0.0, score - penalty)


def calculate_final_score(matched_key_points: int, total_key_points: int, has_anti_points: bool) -> float:
    """Alias retained for readability in evaluation objects."""
    return calculate_question_score(matched_key_points, total_key_points, has_anti_points)


def calculate_document_score(question_scores: Dict[str, float]) -> float:
    """Calculate per-document score as mean(question_scores)."""
    if not question_scores:
        return 0.0
    return sum(question_scores.values()) / len(question_scores)


def assign_verdict(
    matched_key_points: int,
    total_key_points: int,
    has_anti_points: bool,
    is_evasive: bool,
) -> str:
    """Assign one of: correct, partial, incorrect, evasive."""
    if total_key_points <= 0:
        return "incorrect"

    if matched_key_points == 0 and not has_anti_points and is_evasive:
        return "evasive"

    ratio = matched_key_points / total_key_points

    if has_anti_points or ratio < 0.5:
        return "incorrect"
    if ratio >= 1.0:
        return "correct"
    return "partial"


def categorize_consensus(model_evaluations: Dict[str, QuestionEvaluation]) -> str:
    """Categorize consensus for one question across models."""
    verdicts = [ev.verdict for ev in model_evaluations.values()]

    if verdicts and all(v == "correct" for v in verdicts):
        return "all correct"
    if verdicts and all(v == "evasive" for v in verdicts):
        return "all evasive"

    if verdicts and all(v == "incorrect" for v in verdicts):
        signatures = {
            (
                ev.matched_key_points,
                ev.total_key_points,
                tuple(sorted(ev.anti_points_present)),
            )
            for ev in model_evaluations.values()
        }
        if len(signatures) == 1:
            return "all incorrect (same way)"

    return "mixed"


def load_question_set(question_set_path: str) -> QuestionSet:
    """Load and validate question set YAML from file path."""
    path = Path(question_set_path)
    with open(path, "r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}

    question_set = load_question_set_from_dict(payload)
    return question_set


def load_question_set_from_dict(payload: Dict[str, Any]) -> QuestionSet:
    """Load and validate question set from parsed dictionary."""
    for required_field in ["version", "document", "questions"]:
        if required_field not in payload:
            raise QuestionSetValidationError(f"Missing required field: {required_field}")

    questions_raw = payload.get("questions")
    if not isinstance(questions_raw, list):
        raise QuestionSetValidationError("Field 'questions' must be a list")

    questions: List[WholeDocumentQuestion] = []

    for idx, question_data in enumerate(questions_raw):
        location = f"questions[{idx}]"
        for required_field in ["id", "question", "expected"]:
            if required_field not in question_data:
                raise QuestionSetValidationError(f"Missing required field: {location}.{required_field}")

        expected = question_data["expected"] or {}
        if "key_points" not in expected:
            raise QuestionSetValidationError(f"Missing required field: {location}.expected.key_points")

        difficulty = question_data.get("difficulty", "standard")
        if difficulty not in {"basic", "standard", "advanced"}:
            raise QuestionSetValidationError(
                f"Invalid difficulty at {location}.difficulty: {difficulty}. Must be one of basic, standard, advanced"
            )

        key_points = expected.get("key_points") or []
        anti_points = expected.get("anti_points") or []

        if not isinstance(key_points, list):
            raise QuestionSetValidationError(f"Field {location}.expected.key_points must be a list")
        if not isinstance(anti_points, list):
            raise QuestionSetValidationError(f"Field {location}.expected.anti_points must be a list")

        questions.append(
            WholeDocumentQuestion(
                id=str(question_data["id"]),
                question=str(question_data["question"]),
                category=str(question_data.get("category", "general")),
                difficulty=difficulty,
                assertions=question_data.get("assertions"),
                expected=QuestionExpected(
                    key_points=[str(kp) for kp in key_points],
                    anti_points=[str(ap) for ap in anti_points],
                    notes=expected.get("notes"),
                ),
            )
        )

    return QuestionSet(
        version=str(payload["version"]),
        document=str(payload["document"]),
        questions=questions,
        metadata=payload.get("metadata"),
        bulky_source=payload.get("bulky_source"),
        created=payload.get("created"),
        author=payload.get("author"),
        description=payload.get("description"),
    )


class QuestioningStep:
    """Step 5: Whole-document question testing."""

    def __init__(
        self,
        models_config: Dict[str, Any],
        session_config: Optional[Dict[str, Any]] = None,
        judge_model: str = "claude",
    ):
        self.models_config = models_config
        self.session_config = session_config or {}
        self.judge_model = judge_model

    def run(
        self,
        question_set: QuestionSet,
        document_content: str,
        model_names: List[str],
    ) -> QuestioningResult:
        """Run full questioning flow with fresh sessions."""
        # Fresh sessions for Step 5
        session_step = SessionInitStep(self.models_config, self.session_config)
        session_result = session_step.init_sessions(
            document_content=document_content,
            model_names=model_names,
            purpose_prompt=(
                "This document is being tested for comprehension via scenario questions. "
                "Answer using only the provided document context."
            ),
        )

        # Dedicated model manager for this step
        model_manager = ModelManager(self.models_config, self.session_config)
        model_manager.session_manager = session_result.session_manager

        responses: Dict[str, Dict[str, Dict[str, Any]]] = {}
        evaluations: Dict[str, Dict[str, QuestionEvaluation]] = {}
        consensus: Dict[str, str] = {}
        issues: List[Dict[str, Any]] = []
        question_scores: Dict[str, float] = {}

        for question in question_set.questions:
            responses[question.id] = {}
            evaluations[question.id] = {}

            for model_name in model_names:
                prompt = self._build_question_prompt(question)
                response = model_manager.query(model_name, prompt, use_session=True)
                responses[question.id][model_name] = response

                answer_text = _extract_answer_text(response)
                evaluation = self._evaluate_answer(question=question, model_name=model_name, answer_text=answer_text)
                evaluations[question.id][model_name] = evaluation

                if evaluation.verdict != "correct":
                    issue_type = _determine_issue_type(question, evaluation)
                    issues.append(
                        {
                            "question_id": question.id,
                            "model_name": model_name,
                            "verdict": evaluation.verdict,
                            "issue_type": issue_type,
                            "answer_summary": _summarize_text(answer_text),
                            "issue": _build_issue_description(question, evaluation, issue_type),
                            "expected": "; ".join(question.expected.key_points),
                            "question": question.question,
                        }
                    )

            model_scores = [ev.score() for ev in evaluations[question.id].values()]
            question_scores[question.id] = sum(model_scores) / len(model_scores) if model_scores else 0.0
            consensus[question.id] = categorize_consensus(evaluations[question.id])

        document_score = calculate_document_score(question_scores)

        return QuestioningResult(
            question_set=question_set,
            model_names=model_names,
            judge_model=self.judge_model,
            responses=responses,
            evaluations=evaluations,
            question_scores=question_scores,
            document_score=document_score,
            consensus=consensus,
            issues=issues,
        )

    def _evaluate_answer(
        self, question: WholeDocumentQuestion, model_name: str, answer_text: str
    ) -> QuestionEvaluation:
        """Evaluate one answer with LLM-as-Judge."""
        judge_manager = ModelManager(self.models_config, self.session_config)

        judge_prompt = self._build_judge_prompt(question, answer_text)
        judge_response = judge_manager.query(self.judge_model, judge_prompt, use_session=False)
        judge_payload = _parse_judge_payload(judge_response)

        key_point_coverage: Dict[str, bool] = {}
        anti_point_presence: Dict[str, bool] = {}

        for point in question.expected.key_points:
            key_point_coverage[point] = _lookup_boolean_result(judge_payload, "key_points", point)

        for point in question.expected.anti_points:
            anti_point_presence[point] = _lookup_boolean_result(judge_payload, "anti_points", point)

        matched_key_points = sum(1 for matched in key_point_coverage.values() if matched)
        anti_points_present = [point for point, present in anti_point_presence.items() if present]
        is_evasive = bool(judge_payload.get("is_evasive", False))

        verdict = assign_verdict(
            matched_key_points=matched_key_points,
            total_key_points=max(1, len(question.expected.key_points)),
            has_anti_points=bool(anti_points_present),
            is_evasive=is_evasive,
        )

        return QuestionEvaluation(
            question_id=question.id,
            model_name=model_name,
            answer_text=answer_text,
            verdict=verdict,
            matched_key_points=matched_key_points,
            total_key_points=max(1, len(question.expected.key_points)),
            anti_points_present=anti_points_present,
            key_point_coverage=key_point_coverage,
            anti_point_presence=anti_point_presence,
            is_evasive=is_evasive,
            reasoning=str(judge_payload.get("reasoning", "")),
        )

    def _build_question_prompt(self, question: WholeDocumentQuestion) -> str:
        """Build model prompt for the scenario question."""
        return (
            "Answer the following question using only the provided document context from this session. "
            "Be explicit and concise.\n\n"
            f"Question ID: {question.id}\n"
            f"Category: {question.category}\n"
            f"Difficulty: {question.difficulty}\n\n"
            f"{question.question}"
        )

    def _build_judge_prompt(self, question: WholeDocumentQuestion, answer_text: str) -> str:
        """Build LLM-as-Judge prompt for semantic key_point/anti_point evaluation."""
        key_points_block = "\n".join(f"- {point}" for point in question.expected.key_points)
        anti_points_block = "\n".join(f"- {point}" for point in question.expected.anti_points) or "- (none)"

        return f"""You are evaluating one model answer for documentation comprehension.

Question:
{question.question}

Expected key points (must be present semantically):
{key_points_block}

Anti points (must NOT be present semantically):
{anti_points_block}

Model answer:
{answer_text}

Return strict JSON with this schema:
{{
  "key_points": [{{"point": "...", "matched": true|false, "reason": "..."}}],
  "anti_points": [{{"point": "...", "present": true|false, "reason": "..."}}],
  "is_evasive": true|false,
  "reasoning": "short summary"
}}
"""


def _extract_answer_text(response: Dict[str, Any]) -> str:
    """Extract normalized answer text from model response payload."""
    if not isinstance(response, dict):
        return str(response)

    if "raw_response" in response and isinstance(response["raw_response"], str):
        return response["raw_response"]

    try:
        return json.dumps(response, ensure_ascii=False)
    except TypeError:
        return str(response)


def _parse_judge_payload(judge_response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse judge response payload into a normalized dictionary."""
    if isinstance(judge_response, dict):
        if "key_points" in judge_response and "anti_points" in judge_response:
            return judge_response
        raw = judge_response.get("raw_response", "")
    else:
        raw = str(judge_response)

    if not raw:
        return {"key_points": [], "anti_points": [], "is_evasive": False, "reasoning": ""}

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try markdown fenced JSON
    stripped = raw.strip()
    if stripped.startswith("```json"):
        stripped = stripped[7:]
    elif stripped.startswith("```"):
        stripped = stripped[3:]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    stripped = stripped.strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return {"key_points": [], "anti_points": [], "is_evasive": False, "reasoning": "Judge parse failure"}


def _lookup_boolean_result(payload: Dict[str, Any], key: str, point_text: str) -> bool:
    """Find boolean point result in judge payload."""
    entries = payload.get(key, [])
    for entry in entries:
        if str(entry.get("point", "")).strip() == point_text.strip():
            if key == "key_points":
                return bool(entry.get("matched", False))
            return bool(entry.get("present", False))
    return False


def _determine_issue_type(question: WholeDocumentQuestion, evaluation: QuestionEvaluation) -> str:
    """Map evaluation to one of the spec issue types."""
    if "conflict" in question.category.lower() and evaluation.verdict != "correct":
        return "conflict not detected"
    if evaluation.anti_points_present:
        return "false premise accepted"
    if evaluation.verdict == "partial":
        return "partially correct"
    if evaluation.verdict == "evasive":
        return "adversarial failure"
    return "incorrect answer"


def _build_issue_description(question: WholeDocumentQuestion, evaluation: QuestionEvaluation, issue_type: str) -> str:
    """Build issue description for report consumption."""
    missing = [point for point, matched in evaluation.key_point_coverage.items() if not matched]
    anti = evaluation.anti_points_present

    details = [f"Issue type: {issue_type}."]
    if missing:
        details.append(f"Missing key points: {', '.join(missing)}.")
    if anti:
        details.append(f"Included anti points: {', '.join(anti)}.")
    details.append("Improve document clarity around this scenario and expected constraints.")

    return " ".join(details)


def _summarize_text(text: str, max_len: int = 220) -> str:
    """Create short summary text for report issue lines."""
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3] + "..."
