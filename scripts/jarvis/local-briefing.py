#!/usr/bin/env python3
"""Genera briefing local en Mac sin depender de n8n."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("JARVIS_TZ", "America/Guayaquil"))
OWNER = os.environ.get("JARVIS_OWNER", "Andy")


def run_applescript(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def calendar_events() -> list[str]:
    script = r'''
set startOfDay to current date
set hours of startOfDay to 0
set minutes of startOfDay to 0
set seconds of startOfDay to 0
set endOfDay to startOfDay + (1 * days)
set lines to {}

tell application "Calendar"
  repeat with cal in calendars
    try
      repeat with evt in (every event of cal whose start date ≥ startOfDay and start date < endOfDay)
        set eventTime to time string of (start date of evt)
        set eventTitle to summary of evt
        set end of lines to (eventTime & " — " & eventTitle)
      end repeat
    end try
  end repeat
end tell

if (count of lines) is 0 then
  return "Sin eventos en el calendario hoy."
end if

set AppleScript's text item delimiters to linefeed
return lines as text
'''
    raw = run_applescript(script)
    if not raw or raw == "Sin eventos en el calendario hoy.":
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def reminders() -> list[str]:
    script = r'''
set lines to {}
tell application "Reminders"
  repeat with lst in lists
    repeat with r in (reminders of lst whose completed is false)
      if due date of r is not missing value then
        set d to due date of r
        set todayStart to current date
        set time of todayStart to 0
        set todayEnd to todayStart + (1 * days)
        if d ≥ todayStart and d < todayEnd then
          set end of lines to (name of r as text)
        end if
      end if
    end repeat
  end repeat
end tell
if (count of lines) is 0 then return ""
set AppleScript's text item delimiters to linefeed
return lines as text
'''
    raw = run_applescript(script)
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def build_briefing() -> dict[str, str]:
    now = datetime.now(TZ)
    weekday_names = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]
    month_names = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    fecha = (
        f"{weekday_names[now.weekday()]}, "
        f"{now.day} de {month_names[now.month - 1]} de {now.year}"
    )

    events = calendar_events()
    tasks = reminders()

    parts = [
        f"Buenos días, {OWNER}. Hoy es {fecha}.",
        "",
        "Agenda de hoy:",
    ]

    if events:
        for event in events[:8]:
            parts.append(f"- {event}")
    else:
        parts.append("- No tienes eventos en el calendario. Buen día para trabajo profundo.")

    parts.extend(["", "Recordatorios para hoy:"])
    if tasks:
        for task in tasks[:6]:
            parts.append(f"- {task}")
    else:
        parts.append("- Sin recordatorios pendientes con fecha de hoy.")

    parts.extend(
        [
            "",
            "Prioridades Vanguard Scale:",
            "- Revisar leads nuevos y responder en menos de 3 minutos.",
            "- Avanzar onboarding de clientes activos.",
            "- Una acción de crecimiento: contenido, outreach o mejora del funnel.",
            "",
            "Buen día. Estoy aquí cuando necesites el siguiente briefing.",
        ]
    )

    return {
        "title": "Briefing Jarvis",
        "text": "\n".join(parts),
        "generated_at": now.isoformat(),
        "source": "local",
    }


def main() -> int:
    payload = build_briefing()
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
