"""Parsing and view models for official hospital emergency wait pages."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any


class _PageParser(HTMLParser):
    """Extract visible text and table rows from a hospital page."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        if self._ignored_depth:
            return
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in {"th", "td"} and self._row is not None and self._cell is not None:
            self._row.append(_clean(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._table is not None and self._row is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        value = _clean(data)
        if not value:
            return
        self.text_parts.append(value)
        if self._cell is not None:
            self._cell.append(value)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _minutes(value: str) -> int | None:
    if re.search(r"<\s*1\s*(?:hour|hr)", value, re.IGNORECASE):
        return 60
    match = re.search(
        r"(\d+)\s*(hour|hr|minute|min)",
        value,
        re.IGNORECASE,
    )
    if not match:
        return None
    number = int(match.group(1))
    return number * 60 if match.group(2).lower().startswith(("hour", "hr")) else number


def _duration(value: str) -> str | None:
    match = re.search(
        r"<\s*1\s*(?:hour|hr)s?|\d+\s*(?:hours?|hrs?|minutes?|mins?)",
        value,
        re.IGNORECASE,
    )
    return _clean(match.group()) if match else None


def _patients(value: str) -> int | None:
    match = re.search(r"\d+", value.replace(",", ""))
    return int(match.group()) if match else None


def _facility(
    *,
    hospital: str,
    cluster: str,
    category: str,
    patients_waiting: int | None,
    wait_display: str | None,
    wait_minutes: int | None,
    bed_wait_display: str | None = None,
    bed_wait_minutes: int | None = None,
) -> dict[str, Any]:
    return {
        "id": re.sub(r"[^a-z0-9]+", "-", f"{cluster}-{hospital}-{category}".lower()).strip("-"),
        "hospital": hospital,
        "cluster": cluster,
        "category": category,
        "patients_waiting": patients_waiting,
        "wait_to_doctor": wait_display,
        "wait_to_doctor_minutes": wait_minutes,
        "bed_wait": bed_wait_display,
        "bed_wait_minutes": bed_wait_minutes,
    }


def _parse_ttsh(text: str) -> list[dict[str, Any]]:
    """Parse the TTSH emergency queue labels."""
    patients = re.search(
        r"No\.?\s+of\s+Patients\s+Awaiting\s+Consultation\s*:?\s*([\d,]+)",
        text,
        re.IGNORECASE,
    )
    wait = re.search(
        r"Average\s+Consult\s+Wait\s+Time\s*:?\s*([^.;]+)",
        text,
        re.IGNORECASE,
    )
    if not patients and not wait:
        return []
    wait_display = _duration(wait.group(1)) if wait else None
    return [
        _facility(
            hospital="Tan Tock Seng Hospital",
            cluster="NHG",
            category="adult",
            patients_waiting=_patients(patients.group(1)) if patients else None,
            wait_display=wait_display,
            wait_minutes=_minutes(wait_display or ""),
        )
    ]


def _parse_woodlands(text: str) -> list[dict[str, Any]]:
    """Parse the Woodlands Health emergency queue labels."""
    patients = re.search(
        r"Number\s+of\s+patients\s+in\s+queue\s*:?\s*([\d,]+)",
        text,
        re.IGNORECASE,
    )
    wait = re.search(
        r"Waiting\s+time\s+to\s+see\s+doctor\s*:?\s*([^.;]+)",
        text,
        re.IGNORECASE,
    )
    if not patients and not wait:
        return []
    wait_display = _duration(wait.group(1)) if wait else None
    return [
        _facility(
            hospital="Woodlands Health",
            cluster="NHG",
            category="adult",
            patients_waiting=_patients(patients.group(1)) if patients else None,
            wait_display=wait_display,
            wait_minutes=_minutes(wait_display or ""),
        )
    ]


def _parse_nuhs(page: _PageParser) -> list[dict[str, Any]]:
    """Parse NUHS tables, which contain hospitals as columns."""
    hospitals = {
        "Alexandra Hospital",
        "National University Hospital",
        "Ng Teng Fong General Hospital",
    }
    facilities: list[dict[str, Any]] = []
    for table_index, rows in enumerate(page.tables):
        header = next(
            (
                row
                for row in rows
                if any(cell in hospitals for cell in row)
            ),
            None,
        )
        if header is None:
            continue
        columns = [
            (index, cell)
            for index, cell in enumerate(header)
            if cell in hospitals
        ]
        values: dict[str, dict[str, str]] = {name: {} for _, name in columns}
        for row in rows:
            if not row:
                continue
            label = row[0].lower()
            if "patients waiting for consult" in label:
                metric = "patients"
            elif "wait time to see doctor" in label:
                metric = "doctor"
            elif "bed wait time" in label:
                metric = "bed"
            else:
                continue
            for index, hospital in columns:
                if index < len(row):
                    values[hospital][metric] = row[index]
        category = "children" if table_index > 0 else "adult"
        for hospital, metrics in values.items():
            doctor = metrics.get("doctor")
            bed = metrics.get("bed")
            if not metrics:
                continue
            facilities.append(
                _facility(
                    hospital=hospital,
                    cluster="NUHS",
                    category=category,
                    patients_waiting=_patients(metrics.get("patients", "")),
                    wait_display=doctor,
                    wait_minutes=_minutes(doctor or ""),
                    bed_wait_display=bed,
                    bed_wait_minutes=_minutes(bed or ""),
                )
            )
    return facilities


def parse_wait_page(html: str, source: str) -> list[dict[str, Any]]:
    """Parse one official hospital page by its configured source name."""
    page = _PageParser()
    page.feed(html)
    text = _clean(" ".join(page.text_parts))
    if source == "ttsh":
        return _parse_ttsh(text)
    if source == "woodlands":
        return _parse_woodlands(text)
    if source == "nuhs":
        return _parse_nuhs(page)
    return []


def healthcare_view(
    pages: dict[str, str],
    sources: dict[str, dict[str, str]],
    errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Combine source pages into the stable healthcare response shape."""
    facilities: list[dict[str, Any]] = []
    source_status: list[dict[str, Any]] = []
    for source, html in pages.items():
        facilities.extend(parse_wait_page(html, source))
        source_status.append(
            {
                "id": source,
                "name": sources[source]["name"],
                "url": sources[source]["url"],
                "state": "available",
            }
        )
    for source, message in (errors or {}).items():
        source_status.append(
            {
                "id": source,
                "name": sources[source]["name"],
                "url": sources[source]["url"],
                "state": "unavailable",
                "error": message,
            }
        )
    return {
        "facilities": facilities,
        "sources": source_status,
    }
