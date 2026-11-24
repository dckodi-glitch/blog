#!/usr/bin/env python3
"""Reproducibly summarize the UCI household electricity minute data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath


EXPECTED_MEMBER = "household_power_consumption.txt"
EXPECTED_COLUMNS = (
    "Date",
    "Time",
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
)
DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M:%S"
MINUTE = timedelta(minutes=1)
MISSING_MARKER = "?"
NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)?\Z")
DATE_PATTERN = re.compile(r"\d{1,2}/\d{1,2}/\d{4}\Z")
TIME_PATTERN = re.compile(r"\d{2}:\d{2}:\d{2}\Z")


@dataclass
class Hourly:
    observed_minutes: int = 0
    valid_power_minutes: int = 0
    missing_power_minutes: int = 0
    active_power_sum_kw: Decimal = Decimal("0")


@dataclass
class Daily:
    observed_minutes: int = 0
    valid_power_minutes: int = 0
    missing_power_minutes: int = 0
    active_power_sum_kw: Decimal = Decimal("0")
    hourly: dict[int, Hourly] = field(default_factory=dict)


def validate_member_name(name: str) -> None:
    """Reject unsafe or non-canonical archive member paths."""
    if "\\" in name:
        raise ValueError(f"Unsafe archive member path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError(f"Unsafe archive member path: {name!r}")
    if name != EXPECTED_MEMBER:
        raise ValueError(f"Unexpected archive member: {name!r}")


def open_source_member(zip_path: Path) -> tuple[zipfile.ZipFile, zipfile.ZipInfo]:
    archive = zipfile.ZipFile(zip_path)
    try:
        members = archive.infolist()
        if len(members) != 1:
            raise ValueError(
                f"Expected exactly one archive member, found {len(members)}"
            )
        member = members[0]
        validate_member_name(member.filename)
        if member.is_dir():
            raise ValueError("Expected a text file, not an archive directory")
        return archive, member
    except Exception:
        archive.close()
        raise


def parse_timestamp(date_text: str, time_text: str) -> datetime:
    if not DATE_PATTERN.fullmatch(date_text) or not TIME_PATTERN.fullmatch(time_text):
        raise ValueError(
            f"Malformed timestamp: date={date_text!r}, time={time_text!r}"
        )
    try:
        parsed_date = datetime.strptime(date_text, DATE_FORMAT).date()
        parsed_time = datetime.strptime(time_text, TIME_FORMAT).time()
    except ValueError as exc:
        raise ValueError(
            f"Malformed timestamp: date={date_text!r}, time={time_text!r}"
        ) from exc
    if parsed_time.second != 0:
        raise ValueError(f"Timestamp is not minute-aligned: {date_text} {time_text}")
    return datetime.combine(parsed_date, parsed_time)


def parse_power(value: str, line_number: int) -> Decimal | None:
    if value == MISSING_MARKER:
        return None
    if not NUMBER_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid active-power value on line {line_number}: {value!r}")
    try:
        power_kw = Decimal(value.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid active-power value on line {line_number}: {value!r}"
        ) from exc
    if not power_kw.is_finite() or power_kw < 0:
        raise ValueError(f"Invalid active-power value on line {line_number}: {value!r}")
    return power_kw


def expected_minutes_for_date(day: date, first: datetime, last: datetime) -> int:
    """Count minute slots on this date within the inclusive observed period."""
    day_start = datetime.combine(day, time.min)
    day_end = day_start + timedelta(days=1) - MINUTE
    interval_start = max(first, day_start)
    interval_end = min(last, day_end)
    if interval_end < interval_start:
        return 0
    return int((interval_end - interval_start) / MINUTE) + 1


def expected_minutes_for_hour(
    day: date, hour: int, first: datetime, last: datetime
) -> int:
    """Count expected minute slots in a clock hour, clipped to observed bounds."""
    hour_start = datetime.combine(day, time(hour=hour))
    hour_end = hour_start + timedelta(hours=1) - MINUTE
    interval_start = max(first, hour_start)
    interval_end = min(last, hour_end)
    if interval_end < interval_start:
        return 0
    return int((interval_end - interval_start) / MINUTE) + 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def git_provenance(zip_path: Path) -> dict[str, str]:
    root = zip_path.resolve().parent
    relative_zip = zip_path.resolve().relative_to(root).as_posix()
    return {
        "input_commit": git_value(root, "log", "-1", "--format=%H", "--", relative_zip),
        "input_blob_sha": git_value(root, "rev-parse", f"HEAD:{relative_zip}"),
        "analysis_revision": git_value(root, "rev-parse", "HEAD"),
    }


def read_daily(zip_path: Path) -> tuple[dict[date, Daily], dict[str, object]]:
    archive, member = open_source_member(zip_path)
    daily: dict[date, Daily] = defaultdict(Daily)
    first: datetime | None = None
    last: datetime | None = None
    prior: datetime | None = None
    row_count = 0
    missing_power = 0
    gap_events = 0
    skipped_minutes = 0

    try:
        with archive.open(member, "r") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.reader(text, delimiter=";")
            try:
                header = next(reader)
            except StopIteration as exc:
                raise ValueError("The archive member is empty") from exc
            if tuple(header) != EXPECTED_COLUMNS:
                raise ValueError(
                    "Unexpected data columns; expected "
                    + ";".join(EXPECTED_COLUMNS)
                )

            for line_number, row in enumerate(reader, start=2):
                if len(row) != len(EXPECTED_COLUMNS):
                    raise ValueError(
                        f"Malformed row on line {line_number}: "
                        f"expected {len(EXPECTED_COLUMNS)} columns, found {len(row)}"
                    )
                timestamp = parse_timestamp(row[0], row[1])
                if prior is not None:
                    delta = timestamp - prior
                    if delta <= timedelta(0):
                        raise ValueError(
                            f"Duplicate or out-of-order timestamp on line {line_number}: "
                            f"{timestamp}"
                        )
                    if delta % MINUTE:
                        raise ValueError(
                            f"Sampling interval is not a whole minute on line {line_number}"
                        )
                    if delta > MINUTE:
                        gap_events += 1
                        skipped_minutes += int(delta / MINUTE) - 1
                power = parse_power(row[2], line_number)
                day = timestamp.date()
                record = daily[day]
                hour_record = record.hourly.setdefault(timestamp.hour, Hourly())
                record.observed_minutes += 1
                hour_record.observed_minutes += 1
                row_count += 1
                if power is None:
                    record.missing_power_minutes += 1
                    hour_record.missing_power_minutes += 1
                    missing_power += 1
                else:
                    record.valid_power_minutes += 1
                    record.active_power_sum_kw += power
                    hour_record.valid_power_minutes += 1
                    hour_record.active_power_sum_kw += power
                first = timestamp if first is None else first
                last = timestamp
                prior = timestamp
    finally:
        archive.close()

    if row_count == 0 or first is None or last is None:
        raise ValueError("The archive member contains a header but no observations")
    summary: dict[str, object] = {
        "row_count": row_count,
        "first_timestamp": first.isoformat(sep=" "),
        "last_timestamp": last.isoformat(sep=" "),
        "first_date": first.date().isoformat(),
        "last_date": last.date().isoformat(),
        "day_count": len(daily),
        "missing_active_power_minutes": missing_power,
        "missing_active_power_pct": round(100 * missing_power / row_count, 6),
        "timestamp_gap_events": gap_events,
        "skipped_minute_slots": skipped_minutes,
        "duplicate_timestamps": 0,
        "out_of_order_timestamps": 0,
        "timezone": "Not specified by the source; timestamps are kept timezone-naive.",
    }
    return dict(daily), summary


def write_daily_csv(
    path: Path, daily: dict[date, Daily], first: datetime, last: datetime
) -> list[dict[str, object]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "date",
                "daily_energy_kwh",
                "expected_minutes",
                "observed_minutes",
                "valid_power_minutes",
                "missing_power_minutes",
                "observed_coverage_pct",
                "valid_coverage_pct",
                "complete_day",
            )
        )
        day = first.date()
        while day <= last.date():
            record = daily.get(day, Daily())
            expected = expected_minutes_for_date(day, first, last)
            observed_coverage = 100 * record.observed_minutes / expected
            valid_coverage = 100 * record.valid_power_minutes / expected
            complete = expected == 1440 and record.valid_power_minutes == 1440
            energy = record.active_power_sum_kw / Decimal(60)
            row = {
                "date": day.isoformat(),
                "daily_energy_kwh": f"{energy:.6f}",
                "expected_minutes": expected,
                "observed_minutes": record.observed_minutes,
                "valid_power_minutes": record.valid_power_minutes,
                "missing_power_minutes": record.missing_power_minutes,
                "observed_coverage_pct": f"{observed_coverage:.3f}",
                "valid_coverage_pct": f"{valid_coverage:.3f}",
                "complete_day": "true" if complete else "false",
            }
            writer.writerow(row.values())
            rows.append(row)
            day += timedelta(days=1)
    return rows


def write_hourly_csv(
    path: Path, daily: dict[date, Daily], first: datetime, last: datetime
) -> list[dict[str, object]]:
    """Write all 24 clock-hour aggregates; means require at least 90% coverage."""
    grouped = {hour: Hourly() for hour in range(24)}
    expected = {hour: 0 for hour in range(24)}
    day = first.date()
    while day <= last.date():
        for hour in range(24):
            expected[hour] += expected_minutes_for_hour(day, hour, first, last)
            source = daily.get(day, Daily()).hourly.get(hour, Hourly())
            target = grouped[hour]
            target.observed_minutes += source.observed_minutes
            target.valid_power_minutes += source.valid_power_minutes
            target.missing_power_minutes += source.missing_power_minutes
            target.active_power_sum_kw += source.active_power_sum_kw
        day += timedelta(days=1)

    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "hour_of_day",
                "mean_active_power_kw",
                "expected_minutes",
                "observed_minutes",
                "valid_power_minutes",
                "missing_power_minutes",
                "valid_coverage_pct",
                "minimum_valid_minutes",
                "complete_hour",
            )
        )
        for hour in range(24):
            record = grouped[hour]
            expected_count = expected[hour]
            minimum_valid = (expected_count * 9 + 9) // 10
            complete = expected_count > 0 and record.valid_power_minutes >= minimum_valid
            coverage = (
                100 * record.valid_power_minutes / expected_count
                if expected_count
                else 0
            )
            mean_power = (
                f"{record.active_power_sum_kw / record.valid_power_minutes:.6f}"
                if complete
                else ""
            )
            row = {
                "hour_of_day": f"{hour:02d}:00",
                "mean_active_power_kw": mean_power,
                "expected_minutes": expected_count,
                "observed_minutes": record.observed_minutes,
                "valid_power_minutes": record.valid_power_minutes,
                "missing_power_minutes": record.missing_power_minutes,
                "valid_coverage_pct": f"{coverage:.3f}",
                "minimum_valid_minutes": minimum_valid,
                "complete_hour": "true" if complete else "false",
            }
            writer.writerow(row.values())
            rows.append(row)
    return rows


def write_svg(path: Path, rows: list[dict[str, object]]) -> None:
    width, height = 1200, 520
    left, right, top, bottom = 84, 28, 54, 80
    plot_width, plot_height = width - left - right, height - top - bottom
    energies = [float(row["daily_energy_kwh"]) for row in rows]
    maximum = max(energies, default=1.0)
    y_max = max(1.0, math.ceil(maximum / 2) * 2)

    def x_at(index: int) -> float:
        return left + (plot_width * index / max(1, len(rows) - 1))

    def y_at(energy: float) -> float:
        return top + plot_height * (1 - energy / y_max)

    complete_points: list[str] = []
    for index, row in enumerate(rows):
        if row["complete_day"] == "true":
            command = "L" if index > 0 and rows[index - 1]["complete_day"] == "true" else "M"
            complete_points.append(
                f"{command}{x_at(index):.2f},{y_at(float(row['daily_energy_kwh'])):.2f}"
            )

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" '
        f'viewBox="0 0 {width} {height}">',
        "<title id=\"title\">Daily household electricity consumption</title>",
        (
            '<desc id="desc">Historical daily active electricity energy in kilowatt-hours. '
            'Blue line segments show days with all 1440 valid minutes. Orange points mark '
            'partial or lower-coverage days; see the CSV for exact coverage.</desc>'
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="84" y="29" font-family="sans-serif" font-size="21" font-weight="700">'
        "Daily household electricity consumption</text>",
    ]
    for tick in range(0, y_max + 1, max(1, y_max // 4)):
        y = y_at(float(tick))
        elements.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{width-right}" y2="{y:.2f}" '
                'stroke="#e5e7eb"/>',
                f'<text x="{left-12}" y="{y+4:.2f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="12" fill="#374151">{tick}</text>',
            ]
        )
    if complete_points:
        elements.append(
            f'<path d="{" ".join(complete_points)}" fill="none" stroke="#1769aa" '
            'stroke-width="1.2"/>'
        )
    for index, row in enumerate(rows):
        complete = row["complete_day"] == "true"
        energy = str(row["daily_energy_kwh"])
        coverage = str(row["valid_coverage_pct"])
        label = "complete day" if complete else "partial or lower-coverage day"
        elements.append(
            f'<circle class="{"complete-day" if complete else "incomplete-day"}" '
            f'data-date="{row["date"]}" data-daily-energy-kwh="{energy}" '
            f'data-valid-coverage-pct="{coverage}" cx="{x_at(index):.2f}" '
            f'cy="{y_at(float(energy)):.2f}" r="{1 if complete else 2.5}" '
            f'fill="{"#1769aa" if complete else "#c76b00"}" opacity="0.8">'
            f'<title>{row["date"]}: {energy} kWh; valid coverage {coverage}% '
            f'({label})</title></circle>'
        )
    elements.extend(
        [
            f'<line x1="{left}" y1="{top+plot_height}" x2="{width-right}" '
            f'y2="{top+plot_height}" stroke="#111827"/>',
            f'<text x="{left}" y="{height-43}" font-family="sans-serif" font-size="12">'
            f'{rows[0]["date"]}</text>',
            f'<text x="{width-right}" y="{height-43}" text-anchor="end" '
            f'font-family="sans-serif" font-size="12">{rows[-1]["date"]}</text>',
            f'<text x="22" y="{top+plot_height/2}" transform="rotate(-90 22 '
            f'{top+plot_height/2})" text-anchor="middle" font-family="sans-serif" '
            'font-size="13">Daily energy (kWh)</text>',
            f'<text x="{width/2}" y="{height-14}" text-anchor="middle" '
            'font-family="sans-serif" font-size="13">Date (source timestamps; timezone unspecified)</text>',
            '<line x1="770" y1="30" x2="796" y2="30" stroke="#1769aa" stroke-width="2"/>',
            '<text x="803" y="34" font-family="sans-serif" font-size="12">'
            "Complete days (1440 valid minutes)</text>",
            '<circle cx="1030" cy="30" r="3" fill="#c76b00"/>',
            '<text x="1040" y="34" font-family="sans-serif" font-size="12">'
            "Partial / lower coverage</text>",
            "</svg>",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def write_hourly_svg(path: Path, rows: list[dict[str, object]]) -> None:
    width, height = 1200, 520
    left, right, top, bottom = 82, 28, 68, 96
    plot_width, plot_height = width - left - right, height - top - bottom
    values = [
        float(row["mean_active_power_kw"])
        for row in rows
        if row["complete_hour"] == "true"
    ]
    maximum = max(values, default=1.0)
    y_max = max(1.0, math.ceil(maximum / 0.5) * 0.5)
    bar_width = plot_width / len(rows) * 0.62

    def y_at(value: float) -> float:
        return top + plot_height * (1 - value / y_max)

    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" '
        f'viewBox="0 0 {width} {height}">',
        "<title id=\"title\">Average active power by hour of day</title>",
        (
            '<desc id="desc">Mean of valid minute-average active-power readings in '
            'kilowatts, grouped by the source clock hour across the full observation '
            'period. An hour is included only when at least 90 percent of its expected '
            'minute slots have valid readings. Timestamps are timezone-naive.</desc>'
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="82" y="30" font-family="sans-serif" font-size="21" font-weight="700">'
        "Average active power by hour of day</text>",
    ]
    for tick in range(5):
        value = y_max * tick / 4
        y = y_at(value)
        elements.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{width-right}" y2="{y:.2f}" '
                'stroke="#e5e7eb"/>',
                f'<text x="{left-12}" y="{y+4:.2f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="12" fill="#374151">{value:.1f}</text>',
            ]
        )
    for index, row in enumerate(rows):
        center = left + plot_width * (index + 0.5) / len(rows)
        complete = row["complete_hour"] == "true"
        coverage = str(row["valid_coverage_pct"])
        valid = str(row["valid_power_minutes"])
        expected = str(row["expected_minutes"])
        color = "#1769aa" if complete else "#c76b00"
        if complete:
            mean = float(str(row["mean_active_power_kw"]))
            y = y_at(mean)
            elements.append(
                f'<rect x="{center-bar_width/2:.2f}" y="{y:.2f}" '
                f'width="{bar_width:.2f}" height="{top+plot_height-y:.2f}" '
                f'fill="{color}"><title>{row["hour_of_day"]}, mean {mean:.6f} kW; '
                f'{valid} valid of {expected} expected minutes; coverage {coverage}%'
                "</title></rect>"
            )
        else:
            elements.append(
                f'<rect x="{center-bar_width/2:.2f}" y="{top+plot_height-4:.2f}" '
                f'width="{bar_width:.2f}" height="4" fill="{color}">'
                f'<title>{row["hour_of_day"]}: incomplete; {valid} valid of '
                f'{expected} expected minutes; coverage {coverage}%</title></rect>'
            )
        elements.append(
            f'<text x="{center:.2f}" y="{top+plot_height+20}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="11">{row["hour_of_day"][:2]}</text>'
        )
    elements.extend(
        [
            f'<line x1="{left}" y1="{top+plot_height}" x2="{width-right}" '
            f'y2="{top+plot_height}" stroke="#111827"/>',
            f'<text x="22" y="{top+plot_height/2}" transform="rotate(-90 22 '
            f'{top+plot_height/2})" text-anchor="middle" font-family="sans-serif" '
            'font-size="13">Mean active power (kW)</text>',
            f'<text x="{width/2}" y="{height-18}" text-anchor="middle" '
            'font-family="sans-serif" font-size="13">Hour of day (source clock; timezone unspecified)</text>',
            '<rect x="920" y="20" width="12" height="12" fill="#1769aa"/>',
            '<text x="938" y="31" font-family="sans-serif" font-size="12">'
            "Meets 90% valid-coverage rule</text>",
            '<rect x="920" y="39" width="12" height="12" fill="#c76b00"/>',
            '<text x="938" y="50" font-family="sans-serif" font-size="12">'
            "Incomplete (mean omitted)</text>",
            "</svg>",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def run_analysis(zip_path: Path, output_dir: Path) -> dict[str, object]:
    daily, quality = read_daily(zip_path)
    first = datetime.fromisoformat(str(quality["first_timestamp"]))
    last = datetime.fromisoformat(str(quality["last_timestamp"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "daily_consumption.csv"
    svg_path = output_dir / "daily_consumption.svg"
    hourly_csv_path = output_dir / "hourly_active_power.csv"
    hourly_svg_path = output_dir / "hourly_active_power.svg"
    quality_path = output_dir / "quality_summary.json"
    metadata_path = output_dir / "export_metadata.json"

    rows = write_daily_csv(csv_path, daily, first, last)
    write_svg(svg_path, rows)
    hourly_rows = write_hourly_csv(hourly_csv_path, daily, first, last)
    write_hourly_svg(hourly_svg_path, hourly_rows)

    valid_minutes = sum(item.valid_power_minutes for item in daily.values())
    complete_days = sum(row["complete_day"] == "true" for row in rows)
    quality.update(
        {
            "valid_active_power_minutes": valid_minutes,
            "complete_days": complete_days,
            "partial_or_incomplete_days": len(rows) - complete_days,
            "coverage_definition": (
                "Expected minutes are scheduled one-minute timestamp slots from the "
                "first through last observed source timestamp, inclusive; only full "
                "calendar days can be complete. Valid coverage excludes '?' power values."
            ),
            "active_power_missing_marker": MISSING_MARKER,
            "active_power_unit": "kW, minute-average",
            "energy_unit": "kWh",
            "method": "Sum valid Global_active_power values in kW and divide by 60.",
            "hourly_group_count": 24,
            "complete_hour_groups": sum(
                row["complete_hour"] == "true" for row in hourly_rows
            ),
            "incomplete_hour_groups": sum(
                row["complete_hour"] != "true" for row in hourly_rows
            ),
            "hourly_coverage_rule": (
                "A clock-hour group is complete when at least 90% of all expected "
                "minute slots in that source clock hour have valid active-power "
                "readings. Expected slots span the inclusive first-to-last timestamp "
                "period, including timestamp gaps; incomplete group means are omitted."
            ),
            "hourly_time_convention": (
                "Group by the timezone-naive source timestamp clock hour; no timezone "
                "or daylight-saving adjustment is inferred."
            ),
        }
    )
    quality_path.write_text(
        json.dumps(quality, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    provenance = git_provenance(zip_path)
    repo_root = zip_path.resolve().parent
    script_path = Path(__file__).resolve()
    try:
        script_hash = sha256_file(script_path)
    except OSError:
        script_hash = ""
    try:
        dirty = bool(git_value(repo_root, "status", "--porcelain"))
    except subprocess.CalledProcessError:
        dirty = None
    metadata = {
        "project": "Historical household electricity case study",
        "milestone_label": {
            "id": "e03",
            "coverage_date": "2024-08-07",
            "coverage_date_is_execution_date": False,
        },
        "question": (
            "What daily active electricity energy is present in the recorded "
            "minute-average power for one French household, how complete are the "
            "daily observations, and how does mean active power vary by source clock hour?"
        ),
        "observation_period": {
            "first_timestamp": quality["first_timestamp"],
            "last_timestamp": quality["last_timestamp"],
            "timezone": "Not specified; source timestamps kept timezone-naive.",
        },
        "source_vintage": {
            "dataset": "UCI Individual household electric power consumption",
            "donation_date": "2012-08-29",
            "observation_period": "2006-12-16 through 2010-11-26",
            "license": "CC BY 4.0",
        },
        "historical_cutoff": str(quality["last_date"]),
        "source_urls": [
            "https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption",
            "https://doi.org/10.24432/C58K54",
        ],
        "input": {
            "archive": zip_path.resolve().relative_to(repo_root).as_posix(),
            "archive_member": EXPECTED_MEMBER,
            "input_commit": provenance["input_commit"],
            "input_blob_sha": provenance["input_blob_sha"],
            "local_sha256": sha256_file(zip_path),
        },
        "analysis_revision": {
            "git_commit": provenance["analysis_revision"],
            "working_tree_dirty_at_execution": dirty,
            "script_sha256": script_hash,
        },
        "execution_timestamp": datetime.now().astimezone().isoformat(),
        "publication_date": None,
        "method": {
            "sampling": (
                "One source row is expected per minute; timestamps must be minute-aligned "
                "and strictly increasing. Gaps are reported, not filled."
            ),
            "energy": (
                "Global_active_power is a minute-average in kW. Daily kWh is the sum of "
                "valid minute values divided by 60."
            ),
            "hourly_summary": (
                "For each timezone-naive source clock hour, mean active power is the "
                "arithmetic mean of valid minute-average kW readings across the "
                "observation period. The group is marked complete only at >=90% valid "
                "coverage against expected minute slots; otherwise its mean is omitted."
            ),
            "missing_data": (
                "'?' is counted as missing; missing power is not imputed. Coverage "
                "denominators account for partial first/last calendar days."
            ),
            "time_convention": (
                "Use the source's date/time strings without attaching a timezone; none "
                "is specified by the dataset."
            ),
        },
        "limitations": [
            "One historical French household; results do not represent the user's home or households generally.",
            "Daily and hour-of-day aggregate active power cannot identify appliance use, household behavior, or savings.",
            "Missing active-power minutes are excluded from energy sums and reduce valid coverage.",
            "No forecasting, causal inference, or tariff estimate is included.",
        ],
        "outputs": {
            name: path.relative_to(repo_root).as_posix()
            for name, path in (
                ("daily_csv", csv_path.resolve()),
                ("hourly_csv", hourly_csv_path.resolve()),
                ("quality_summary", quality_path.resolve()),
                ("visualization_svg", svg_path.resolve()),
                ("hourly_visualization_svg", hourly_svg_path.resolve()),
                ("metadata", metadata_path.resolve()),
            )
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {
        "rows": rows,
        "hourly_rows": hourly_rows,
        "quality": quality,
        "metadata": metadata,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    repository = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--zip",
        type=Path,
        default=repository / "individual+household+electric+power+consumption.zip",
        help="source ZIP (default: repository archive)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repository / "outputs",
        help="directory for CSV, JSON, and SVG exports",
    )
    args = parser.parse_args(argv)
    try:
        result = run_analysis(args.zip, args.output_dir)
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        return 2
    print(
        f"Wrote {len(result['rows'])} daily rows and "
        f"{len(result['hourly_rows'])} hourly groups; "
        f"{result['quality']['complete_days']} complete days and "
        f"{result['quality']['complete_hour_groups']} complete hour groups."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
