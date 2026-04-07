from __future__ import annotations

import json
import os

import time
from typing import Any

from src.types import SQLGenerationOutput, AnswerGenerationOutput

DEFAULT_MODEL = "openai/gpt-5-nano"


class OpenRouterLLMClient:
    """LLM client using the OpenRouter SDK for chat completions."""

    provider_name = "openrouter"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        try:
            from openrouter import OpenRouter
        except ModuleNotFoundError as exc:
            raise RuntimeError("Missing dependency: install 'openrouter'.") from exc
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        self._client = OpenRouter(api_key=api_key)
        self._stats = {"llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _chat(self, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        res = self._client.chat.send(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        self._stats["llm_calls"] += 1

        usage = getattr(res, "usage", None)
        if usage is not None:
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            total_tokens = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)

            self._stats["prompt_tokens"] += int(prompt_tokens)
            self._stats["completion_tokens"] += int(completion_tokens)
            self._stats["total_tokens"] += int(total_tokens)

        choices = getattr(res, "choices", None) or []
        if not choices:
            raise RuntimeError("OpenRouter response contained no choices.")

        content = getattr(getattr(choices[0], "message", None), "content", None)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []

            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue

                text_value = getattr(item, "text", None)
                if isinstance(text_value, str):
                    parts.append(text_value)
                    continue

                if isinstance(item, dict):
                    maybe_text = item.get("text")
                    if isinstance(maybe_text, str):
                        parts.append(maybe_text)

            merged = "\n".join(p.strip() for p in parts if p and p.strip())
            if merged:
                return merged

        raise RuntimeError(f"OpenRouter response content has unsupported type: {type(content)!r}")

    @staticmethod
    def _extract_sql(text: str) -> str | None:
        text = text.strip()

        # 1. JSON case
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = json.loads(text)
                sql = parsed.get("sql")
                if isinstance(sql, str) and sql.strip():
                    return sql.strip()
            except json.JSONDecodeError:
                pass

        # 2. ```sql ... ``` block
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                part = part.strip()
                if part.lower().startswith("sql"):
                    return part[3:].strip()
                if any(kw in part.lower() for kw in ["select", "delete", "update", "insert", "drop"]):
                    return part.strip()

        # 3. fallback — znajdź pierwsze słowo SQL
        keywords = ["select", "delete", "update", "insert", "drop"]
        lower = text.lower()

        for kw in keywords:
            idx = lower.find(kw)
            if idx >= 0:
                return text[idx:].strip()

        return None

    def generate_sql(self, question: str, context: dict) -> SQLGenerationOutput:
        system_prompt = (
            "Generate SQLite SELECT queries from natural language questions. "
            "Table: gaming_mental_health. Columns: age, gender, income, daily_gaming_hours, weekly_sessions, years_gaming, sleep_hours, caffeine_intake, exercise_hours, stress_level, anxiety_score, depression_score, social_interaction_score, relationship_satisfaction, academic_performance, work_productivity, addiction_level, multiplayer_ratio, toxic_exposure, violent_games_ratio, mobile_gaming_ratio, night_gaming_ratio, weekend_gaming_hours, friends_gaming_count, online_friends, streaming_hours, esports_interest, headset_usage, microtransactions_spending, parental_supervision, loneliness_score, aggression_score, happiness_score, bmi, screen_time_total, eye_strain_score, back_pain_score, competitive_rank, internet_quality. "
            "Answer analytical questions using aggregation (AVG, COUNT) and GROUP BY; if a grouping column is a continuous numeric variable, bucket it with ROUND or FLOOR before grouping and include sample size (COUNT); for questions about highest or top ranges, determine the threshold dynamically using expressions like MAX(column) * 0.9 instead of hardcoding values; for questions about shares or proportions, compute ratios using COUNT(*) divided by total COUNT(*) and define thresholds dynamically when needed (e.g. MAX(column) * 0.3 for low ranges); avoid raw row outputs unless explicitly requested. "
            "Example: for 'How many users are in the highest income range?', use SELECT COUNT(*) FROM gaming_mental_health WHERE income >= (SELECT MAX(income) * 0.9 FROM gaming_mental_health). "
            "Example: for 'What share of users have low income?', use SELECT COUNT(*) * 1.0 / (SELECT COUNT(*) FROM gaming_mental_health) FROM gaming_mental_health WHERE income < (SELECT MAX(income) * 0.3 FROM gaming_mental_health). "
            "Example: for 'How does stress level change with daily gaming hours?', use SELECT ROUND(daily_gaming_hours, 1) AS gaming_bucket, AVG(stress_level) AS average_stress, COUNT(*) AS sample_size FROM gaming_mental_health GROUP BY gaming_bucket ORDER BY gaming_bucket. "
            "When using grouped or bucketed values (e.g. age groups), describe them as ranges (e.g. 20–29) instead of single values.\n"
            "Focus on describing overall patterns rather than ranking groups unless the difference is clearly significant."
            "If a question includes terms like 'bucket', always group continuous variables into buckets using ROUND or FLOOR instead of grouping by raw values. Example: Q: Which addiction level bucket has the most respondents? A: SELECT ROUND(addiction_level, 1) AS addiction_bucket, COUNT(*) AS respondent_count FROM gaming_mental_health GROUP BY addiction_bucket ORDER BY respondent_count DESC LIMIT 1;"
            "If a metric includes a baseline value like 0 that represents absence of the behavior, consider excluding it when identifying the most common non-zero bucket unless the question explicitly includes it."
            "For questions asking about general trends or comparisons (e.g. 'do younger users have higher values'), answer directly with a clear conclusion (e.g. 'yes', 'no', or 'no clear trend') followed by a brief explanation based on the aggregated data, instead of listing or ranking groups."
            "When creating age or numeric ranges, prefer FLOOR over ROUND to ensure consistent bucket boundaries."
        )   
        user_prompt = f"Question: {question}\n\nGenerate the SQL query only."

        start = time.perf_counter()
        error = None
        sql = None

        try:
            text = self._chat(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.0,
                max_tokens=800,
            )

            sql = self._extract_sql(text)
        except Exception as exc:
            error = str(exc)

        timing_ms = (time.perf_counter() - start) * 1000
        llm_stats = self.pop_stats()
        llm_stats["model"] = self.model

        return SQLGenerationOutput(
            sql=sql,
            timing_ms=timing_ms,
            llm_stats=llm_stats,
            error=error,
        )

    def generate_answer(self, question: str, sql: str | None, rows: list[dict[str, Any]]) -> AnswerGenerationOutput:
        if not sql:
            return AnswerGenerationOutput(
                answer="I cannot answer this with the available table and schema. Please rephrase using known survey fields.",
                timing_ms=0.0,
                llm_stats={"llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": self.model},
                error=None,
            )
        if not rows:
            return AnswerGenerationOutput(
                answer="Query executed, but no rows were returned.",
                timing_ms=0.0,
                llm_stats={"llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": self.model},
                error=None,
            )

        system_prompt = (
            "You are a concise analytics assistant. "
            "Use only the provided SQL results. Do not invent data."
        )
        user_prompt = (
            f"Question:\n{question}\n\nSQL:\n{sql}\n\n"
            f"Rows (JSON):\n{json.dumps(rows[:100], ensure_ascii=True)}\n\n"
            "Write a concise answer in plain English."
        )

        start = time.perf_counter()
        error = None
        answer = ""

        try:
            answer = self._chat(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.2,
                max_tokens=800,
            )
        except Exception as exc:
            error = str(exc)
            answer = f"Error generating answer: {error}"

        timing_ms = (time.perf_counter() - start) * 1000
        llm_stats = self.pop_stats()
        llm_stats["model"] = self.model

        return AnswerGenerationOutput(
            answer=answer,
            timing_ms=timing_ms,
            llm_stats=llm_stats,
            error=error,
        )

    def pop_stats(self) -> dict[str, Any]:
        out = dict(self._stats or {})
        self._stats = {"llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        return out


def build_default_llm_client() -> OpenRouterLLMClient:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required.")
    return OpenRouterLLMClient(api_key=api_key)
