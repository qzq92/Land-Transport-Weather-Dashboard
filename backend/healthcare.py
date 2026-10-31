"""Parsing and view models for official hospital emergency wait pages."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, ClassVar


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

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
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


class _QueueCardParser(HTMLParser):
    """Extract text from NHG emergency queue metric cards."""

    _CARD_CLASSES: ClassVar[set[str]] = {
        "s-edq-primary-card__block",
        "s-edq-primary-card",
    }

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._block: list[str] | None = None
        self._depth = 0
        self._tag = ""

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        class_name = dict(attrs).get("class") or ""
        classes = set(class_name.split())
        if self._block is None and classes & self._CARD_CLASSES:
            self._block = []
            self._depth = 1
            self._tag = tag
        elif self._block is not None and tag == self._tag:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._block is None or tag != self._tag:
            return
        self._depth -= 1
        if self._depth == 0:
            self.blocks.append(_clean(" ".join(self._block)))
            self._block = None
            self._tag = ""

    def handle_data(self, data: str) -> None:
        if self._block is not None:
            value = _clean(data)
            if value:
                self._block.append(value)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _minutes(value: str) -> int | None:
    if re.search(r"<\s*1\s*(?:hour|hr)", value, re.IGNORECASE):
        return 60
    match = re.search(
        r"(\d+)\s*(hours?|hrs?|minutes?|mins?|mis)",
        value,
        re.IGNORECASE,
    )
    if not match:
        return None
    number = int(match.group(1))
    unit = match.group(2).lower()
    return number * 60 if unit.startswith(("hour", "hr")) else number


def _duration(value: str) -> str | None:
    match = re.search(
        r"<\s*1\s*(?:hour|hr)s?|\d+\s*(?:hours?|hrs?|minutes?|mins?|mis)",
        value,
        re.IGNORECASE,
    )
    if not match:
        return None
    display = _clean(match.group())
    return re.sub(r"\bmis\b", "mins", display, flags=re.IGNORECASE)


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
    updated_at: str | None = None,
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
        "updated_at": updated_at,
    }


_NHG_PATIENT_LABEL = re.compile(
    r"no\.?\s*of\s+patients awaiting consultation|"
    r"number of patients waiting(?: to be seen)?|"
    r"number of patients in queue",
    re.IGNORECASE,
)
_NHG_WAIT_LABEL = re.compile(
    r"average consult wait time|"
    r"estimated waiting time to see doctor|"
    r"waiting time to see doctor",
    re.IGNORECASE,
)
_NHG_ANY_LABEL = re.compile(
    rf"(?:{_NHG_PATIENT_LABEL.pattern}|{_NHG_WAIT_LABEL.pattern})",
    re.IGNORECASE,
)
_NHG_PATIENT_VALUE = re.compile(r"([\d,]+)\s*(?:patients?)?", re.IGNORECASE)
_NHG_WAIT_VALUE = re.compile(
    r"([\d,]+)\s*(?:minutes?|mins?|mis)|<\s*1\s*(?:hour|hr)s?",
    re.IGNORECASE,
)
_LAST_UPDATED = re.compile(r"last updated at\s+", re.IGNORECASE)
_REFRESH_WORD = re.compile(r"\brefresh\b", re.IGNORECASE)
_TOKEN_DATE = re.compile(
    r"last[_-]?updated[_-]?date[^>]*>\s*([^<#][^<]*)",
    re.IGNORECASE,
)
_TOKEN_TIME = re.compile(
    r"last[_-]?updated[_-]?time[^>]*>\s*([^<#][^<]*)",
    re.IGNORECASE,
)
_TOKEN_JSON_VALUE = r"(?:\{\s*['\"]value['\"]\s*:\s*)?['\"]([^'\"#]+)['\"]"
_TOKEN_JSON_DATE = re.compile(
    rf"['\"]last[_-]?updated[_-]?date['\"]\s*[:=]\s*{_TOKEN_JSON_VALUE}",
    re.IGNORECASE,
)
_TOKEN_JSON_TIME = re.compile(
    rf"['\"]last[_-]?updated[_-]?time['\"]\s*[:=]\s*{_TOKEN_JSON_VALUE}",
    re.IGNORECASE,
)
_TOKEN_PLACEHOLDER_DATE = re.compile(r"##last_Updated_Date##", re.IGNORECASE)
_TOKEN_PLACEHOLDER_TIME = re.compile(r"##last_Updated_Time##", re.IGNORECASE)
_DATETIME_VALUE = re.compile(
    r"(?:"
    r"\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?"
    r"|"
    r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?"
    r")",
    re.IGNORECASE,
)
_LABELLED_WINDOW = 160


def _value_after_label(
    text: str,
    label: re.Pattern[str],
    value: re.Pattern[str],
) -> str | None:
    match = label.search(text)
    if not match:
        return None
    rest = text[match.end() :]
    next_label = _NHG_ANY_LABEL.search(rest)
    window = rest[: next_label.start()] if next_label else rest
    found = value.search(window)
    return found.group(0) if found else None


def _is_patient_card(text: str) -> bool:
    return bool(
        re.search(
            r"patients awaiting consultation|"
            r"number of patients waiting|"
            r"number of patients in queue|"
            r"\bpatients?\b",
            text,
            re.IGNORECASE,
        )
    ) and not bool(_NHG_WAIT_VALUE.search(text))


def _is_wait_card(text: str) -> bool:
    return bool(
        re.search(
            r"average consult wait time|"
            r"waiting time to see doctor|"
            r"\bmi(?:n|ns|s)\b",
            text,
            re.IGNORECASE,
        )
    )


def _usable_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = _clean(re.sub(r"<[^>]+>", " ", value)).rstrip(" .")
    if not cleaned or "##" in cleaned:
        return None
    return cleaned


def _token_value(html: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(html)
    return _usable_timestamp(match.group(1)) if match else None


def _datetime_from_text(text: str) -> str | None:
    """Return the first date-and-time stamp in ``text``, if present."""
    found = _DATETIME_VALUE.search(text)
    return _usable_timestamp(found.group(0)) if found else None


def _cms_tokens(html: str) -> tuple[str | None, str | None]:
    """Read CMS date and time tokens from markup or Sitecore JSON."""
    date = _token_value(html, _TOKEN_DATE) or _token_value(html, _TOKEN_JSON_DATE)
    time = _token_value(html, _TOKEN_TIME) or _token_value(html, _TOKEN_JSON_TIME)
    return date, time


def _labelled_update_window(text: str) -> str | None:
    """Return the short sentence after "last updated at", before Refresh."""
    labelled = _LAST_UPDATED.search(text)
    if not labelled:
        return None
    window = text[labelled.end() : labelled.end() + _LABELLED_WINDOW]
    refresh = _REFRESH_WORD.search(window)
    if refresh:
        window = window[: refresh.start()]
    return window


def _updated_at(html: str) -> str | None:
    """Read the datetime that follows the page's "last updated at" label.

    Only the date and time are kept. Trailing copy after that stamp, such as
    "Refresh." or NUHS disclaimer text, is discarded. When the labelled
    sentence still contains CMS placeholders, those tokens are filled from
    Sitecore date/time fields on the same page.
    """
    text = _clean(re.sub(r"<[^>]+>", " ", html))
    window = _labelled_update_window(text)
    date, time = _cms_tokens(html)
    if window:
        filled = window
        if date:
            filled = _TOKEN_PLACEHOLDER_DATE.sub(date, filled)
        if time:
            filled = _TOKEN_PLACEHOLDER_TIME.sub(time, filled)
        value = _datetime_from_text(filled)
        if value:
            return value
    if date and time:
        return f"{date} {time}"
    if date:
        return date
    return None


def _parse_nhg_queue_cards(html: str, *, hospital: str) -> list[dict[str, Any]]:
    """Parse NHG queue cards first, then labelled page text."""
    queue_parser = _QueueCardParser()
    queue_parser.feed(html)
    patient_source = next(
        (block for block in queue_parser.blocks if _is_patient_card(block)),
        None,
    )
    wait_source = next(
        (block for block in queue_parser.blocks if _is_wait_card(block)),
        None,
    )
    text = _clean(re.sub(r"<[^>]+>", " ", html))
    if patient_source is None:
        patient_source = _value_after_label(text, _NHG_PATIENT_LABEL, _NHG_PATIENT_VALUE)
    elif _patients(patient_source) is None:
        patient_source = (
            _value_after_label(patient_source, _NHG_PATIENT_LABEL, _NHG_PATIENT_VALUE)
            or patient_source
        )
    if wait_source is None:
        wait_source = _value_after_label(text, _NHG_WAIT_LABEL, _NHG_WAIT_VALUE)
    elif _duration(wait_source) is None:
        wait_source = (
            _value_after_label(wait_source, _NHG_WAIT_LABEL, _NHG_WAIT_VALUE)
            or wait_source
        )
    wait_display = _duration(wait_source or "")
    patients = _patients(patient_source or "")
    if patients is None and wait_display is None:
        return []
    return [
        _facility(
            hospital=hospital,
            cluster="NHG",
            category="adult",
            patients_waiting=patients,
            wait_display=wait_display,
            wait_minutes=_minutes(wait_source or ""),
            updated_at=_updated_at(html),
        )
    ]


def _parse_ttsh(html: str) -> list[dict[str, Any]]:
    """Parse the TTSH emergency queue labels."""
    return _parse_nhg_queue_cards(html, hospital="Tan Tock Seng Hospital")


def _parse_woodlands(html: str) -> list[dict[str, Any]]:
    """Parse the Woodlands Health emergency queue labels."""
    return _parse_nhg_queue_cards(html, hospital="Woodlands Health")


def _parse_ktph(html: str) -> list[dict[str, Any]]:
    """Parse the Khoo Teck Puat Hospital A&E queue labels."""
    return _parse_nhg_queue_cards(html, hospital="Khoo Teck Puat Hospital")


def _parse_nuhs(page: _PageParser, html: str) -> list[dict[str, Any]]:
    """Parse NUHS tables, which contain hospitals as columns."""
    updated_at = _updated_at(html)
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
                    updated_at=updated_at,
                )
            )
    return facilities


def parse_wait_page(html: str, source: str) -> list[dict[str, Any]]:
    """Parse one official hospital page by its configured source name."""
    page = _PageParser()
    page.feed(html)
    if source == "ttsh":
        return _parse_ttsh(html)
    if source == "woodlands":
        return _parse_woodlands(html)
    if source == "ktph":
        return _parse_ktph(html)
    if source == "nuhs":
        return _parse_nuhs(page, html)
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
        parsed = parse_wait_page(html, source)
        source_url = sources[source]["url"]
        for facility in parsed:
            facility["source_url"] = source_url
        facilities.extend(parsed)
        source_status.append(
            {
                "id": source,
                "name": sources[source]["name"],
                "url": source_url,
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
