"""Condition evaluator for proactive watchers - determines when triggers fire."""

import re
import json
import hashlib
import logging
from typing import Any, Optional

logger = logging.getLogger("proactive-watchers.condition")


class ConditionEvaluator:
    """Evaluates watcher conditions against HTTP responses to determine trigger state."""

    SUPPORTED_CONDITIONS = [
        "value_changed",
        "new_item",
        "status_code_change",
        "text_contains",
        "value_exceeds",
        "regex_match",
        "content_hash_changed",
    ]

    def evaluate(self, watcher: dict, response_data: Any, status_code: int,
                 previous_state: dict) -> dict:
        """
        Evaluate a watcher's condition against a response.

        Returns:
            dict with keys:
                triggered (bool): Whether the condition was met
                reason (str): Human-readable explanation
                new_state (dict): State to persist for next evaluation
                extracted_value (Any): The value that was evaluated
        """
        condition = watcher.get("condition", "value_changed")
        trigger_field = watcher.get("trigger_field")

        current_value = self._extract_value(response_data, trigger_field)

        evaluator = getattr(self, f"_eval_{condition}", None)
        if evaluator is None:
            return {
                "triggered": False,
                "reason": f"Unknown condition type: {condition}",
                "new_state": previous_state,
                "extracted_value": current_value,
            }

        try:
            return evaluator(watcher, current_value, response_data, status_code, previous_state)
        except Exception as e:
            logger.error(f"Condition evaluation error for '{watcher.get('name')}': {e}")
            return {
                "triggered": False,
                "reason": f"Evaluation error: {e}",
                "new_state": previous_state,
                "extracted_value": current_value,
            }

    def _extract_value(self, data: Any, field_path: Optional[str]) -> Any:
        """Extract a value from response data using dot-notation field path."""
        if field_path is None:
            return data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data

        parts = field_path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)):
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return current

    def _eval_value_changed(self, watcher, current_value, response_data,
                            status_code, previous_state) -> dict:
        """Trigger when the monitored value changes from the previous poll."""
        prev_value = previous_state.get("last_value")
        is_first_poll = "last_value" not in previous_state

        serialized_current = json.dumps(current_value, sort_keys=True, default=str)
        serialized_prev = json.dumps(prev_value, sort_keys=True, default=str) if not is_first_poll else None

        triggered = not is_first_poll and serialized_current != serialized_prev

        return {
            "triggered": triggered,
            "reason": "Value changed" if triggered else ("Initial poll (baseline)" if is_first_poll else "No change"),
            "new_state": {**previous_state, "last_value": current_value},
            "extracted_value": current_value,
        }

    def _eval_new_item(self, watcher, current_value, response_data,
                       status_code, previous_state) -> dict:
        """Trigger when a new item appears in an array response."""
        if not isinstance(current_value, list):
            return {
                "triggered": False,
                "reason": "Target value is not an array",
                "new_state": previous_state,
                "extracted_value": current_value,
            }

        id_field = watcher.get("id_field", "id")
        current_ids = set()
        for item in current_value:
            if isinstance(item, dict):
                current_ids.add(str(item.get(id_field, json.dumps(item, sort_keys=True))))
            else:
                current_ids.add(str(item))

        prev_ids = set(previous_state.get("known_ids", []))
        is_first_poll = "known_ids" not in previous_state
        new_ids = current_ids - prev_ids

        return {
            "triggered": bool(new_ids) and not is_first_poll,
            "reason": f"{len(new_ids)} new item(s)" if new_ids and not is_first_poll else (
                "Initial poll (baseline)" if is_first_poll else "No new items"
            ),
            "new_state": {**previous_state, "known_ids": list(current_ids)},
            "extracted_value": current_value,
        }

    def _eval_status_code_change(self, watcher, current_value, response_data,
                                 status_code, previous_state) -> dict:
        """Trigger when the HTTP status code changes."""
        prev_code = previous_state.get("last_status_code")
        is_first_poll = prev_code is None

        expected_from = watcher.get("expected_from")
        expected_to = watcher.get("expected_to")

        triggered = False
        if not is_first_poll and status_code != prev_code:
            if expected_from and expected_to:
                triggered = prev_code == expected_from and status_code == expected_to
            elif expected_to:
                triggered = status_code == expected_to
            else:
                triggered = True

        return {
            "triggered": triggered,
            "reason": f"Status changed: {prev_code} → {status_code}" if triggered else (
                "Initial poll" if is_first_poll else f"Status unchanged: {status_code}"
            ),
            "new_state": {**previous_state, "last_status_code": status_code},
            "extracted_value": status_code,
        }

    def _eval_text_contains(self, watcher, current_value, response_data,
                            status_code, previous_state) -> dict:
        """Trigger when response text contains a specified string."""
        search_text = watcher.get("search_text", "")
        case_sensitive = watcher.get("case_sensitive", False)

        text = str(current_value) if current_value is not None else str(response_data)

        if case_sensitive:
            found = search_text in text
        else:
            found = search_text.lower() in text.lower()

        was_found = previous_state.get("text_was_found", False)
        trigger_on = watcher.get("trigger_on", "found")

        if trigger_on == "found":
            triggered = found and not was_found
        elif trigger_on == "not_found":
            triggered = not found and was_found
        else:
            triggered = found

        return {
            "triggered": triggered,
            "reason": f"Text '{search_text}' {'found' if found else 'not found'}" + (
                " (newly)" if triggered else ""
            ),
            "new_state": {**previous_state, "text_was_found": found},
            "extracted_value": text[:500],
        }

    def _eval_value_exceeds(self, watcher, current_value, response_data,
                            status_code, previous_state) -> dict:
        """Trigger when a numeric value exceeds a threshold."""
        threshold = watcher.get("threshold")
        if threshold is None:
            return {
                "triggered": False,
                "reason": "No threshold configured",
                "new_state": previous_state,
                "extracted_value": current_value,
            }

        try:
            numeric_value = float(current_value)
            threshold = float(threshold)
        except (TypeError, ValueError):
            return {
                "triggered": False,
                "reason": f"Cannot compare: value={current_value}, threshold={threshold}",
                "new_state": previous_state,
                "extracted_value": current_value,
            }

        comparator = watcher.get("comparator", "gt")
        comparisons = {
            "gt": numeric_value > threshold,
            "gte": numeric_value >= threshold,
            "lt": numeric_value < threshold,
            "lte": numeric_value <= threshold,
            "eq": numeric_value == threshold,
            "neq": numeric_value != threshold,
        }
        triggered = comparisons.get(comparator, False)

        was_triggered = previous_state.get("threshold_exceeded", False)
        trigger_mode = watcher.get("trigger_mode", "on_change")
        if trigger_mode == "on_change":
            triggered = triggered and not was_triggered

        return {
            "triggered": triggered,
            "reason": f"Value {numeric_value} {comparator} {threshold}" if triggered else f"Value {numeric_value} within threshold",
            "new_state": {**previous_state, "threshold_exceeded": comparisons.get(comparator, False)},
            "extracted_value": numeric_value,
        }

    def _eval_regex_match(self, watcher, current_value, response_data,
                          status_code, previous_state) -> dict:
        """Trigger when response matches a regex pattern."""
        pattern = watcher.get("pattern", "")
        text = str(current_value) if current_value is not None else str(response_data)

        flags = 0
        if not watcher.get("case_sensitive", False):
            flags |= re.IGNORECASE

        match = re.search(pattern, text, flags)
        was_matching = previous_state.get("regex_matched", False)

        trigger_on = watcher.get("trigger_on", "match")
        if trigger_on == "match":
            triggered = bool(match) and not was_matching
        elif trigger_on == "no_match":
            triggered = not match and was_matching
        else:
            triggered = bool(match)

        return {
            "triggered": triggered,
            "reason": f"Pattern {'matched' if match else 'not matched'}: {pattern}",
            "new_state": {
                **previous_state,
                "regex_matched": bool(match),
                "last_match": match.group(0) if match else None,
            },
            "extracted_value": match.group(0) if match else None,
        }

    def _eval_content_hash_changed(self, watcher, current_value, response_data,
                                   status_code, previous_state) -> dict:
        """Trigger when the content hash changes (for binary or large responses)."""
        content = json.dumps(response_data, sort_keys=True, default=str)
        current_hash = hashlib.sha256(content.encode()).hexdigest()
        prev_hash = previous_state.get("content_hash")
        is_first_poll = prev_hash is None

        triggered = not is_first_poll and current_hash != prev_hash

        return {
            "triggered": triggered,
            "reason": "Content hash changed" if triggered else (
                "Initial poll (baseline)" if is_first_poll else "Content unchanged"
            ),
            "new_state": {**previous_state, "content_hash": current_hash},
            "extracted_value": current_hash,
        }
