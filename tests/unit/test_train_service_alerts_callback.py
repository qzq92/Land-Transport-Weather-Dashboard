import unittest
from datetime import datetime, timezone

from callbacks.train_service_alerts_callback import (
    format_mrt_line_operational_details,
    format_rail_status_freshness,
    format_rail_status_summary,
)


def component_text(component):
    """Collect text recursively from a Dash component tree."""
    if component is None:
        return ""
    if isinstance(component, (str, int, float)):
        return str(component)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        return " ".join(component_text(child) for child in children)
    return component_text(children)


class TestTrainServiceAlertsCallback(unittest.TestCase):
    def test_format_mrt_line_operational_details_uses_status_text_override(self):
        mrt_display, _lrt_display = format_mrt_line_operational_details(
            data={},
            line_status_map_override={
                "NSL": {"status": 2, "has_message": True, "status_text": "Delay"}
            },
        )

        first_line_card = mrt_display.children[0]
        status_label = first_line_card.children[1]
        self.assertEqual(status_label.children, "! Delay")

    def test_all_normal_summary_is_concise(self):
        summary = format_rail_status_summary({}, availability="current")

        self.assertEqual(component_text(summary), "✓ All lines operating normally")

    def test_affected_summary_prioritises_impacted_lines(self):
        summary = format_rail_status_summary(
            {
                "NSL": {
                    "status": 2,
                    "status_text": "Service disruption",
                    "reason": "Track fault",
                },
                "EWL": {
                    "status": 1,
                    "status_text": "Delay",
                    "reason": "Longer waiting time",
                },
            }
        )

        self.assertEqual(summary.role, "status")
        self.assertEqual(summary.to_plotly_json()["props"]["aria-live"], "polite")
        self.assertIn("2 lines affected", component_text(summary))
        self.assertIn("NSL — Service disruption", component_text(summary))
        self.assertIn("EWL — Delay", component_text(summary))
        self.assertNotIn("*", component_text(summary))

    def test_unavailable_state_does_not_claim_normal_service(self):
        summary = format_rail_status_summary({}, availability="unavailable")
        mrt_display, lrt_display = format_mrt_line_operational_details(
            None, line_status_map_override={}, availability="unavailable"
        )

        self.assertEqual(component_text(summary), "? Data unavailable")
        self.assertIn("Status unavailable", component_text(mrt_display))
        self.assertIn("Status unavailable", component_text(lrt_display))
        self.assertEqual(len(mrt_display.children), 6)
        self.assertEqual(len(lrt_display.children), 3)

    def test_line_badges_choose_contrasting_text(self):
        mrt_display, _lrt_display = format_mrt_line_operational_details({})
        circle_line_badge = mrt_display.children[2].children[0]

        self.assertEqual(circle_line_badge.style["color"], "#111827")

    def test_freshness_distinguishes_current_partial_and_stale(self):
        updated_at = datetime(2026, 9, 12, 11, 30, tzinfo=timezone.utc)

        current = format_rail_status_freshness(updated_at, "current")
        partial = format_rail_status_freshness(updated_at, "partial")
        stale = format_rail_status_freshness(updated_at, "stale")

        self.assertTrue(current.startswith("Updated "))
        self.assertTrue(partial.startswith("Partial data · Updated "))
        self.assertTrue(stale.startswith("Last known status · Updated "))
        self.assertEqual(
            format_rail_status_freshness(None, "unavailable"),
            "Data unavailable",
        )
