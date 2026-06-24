from datetime import datetime


def export_txt(path: str, results: list, events: list[dict]):
    """Export analysis results to a plain text file.

    Args:
        path: Output file path.
        results: List of analysis result dicts (or error strings).
        events: List of event dicts corresponding to results.
    """
    lines = [
        "=== WinLog Analyzer - Raport ===",
        f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Liczba zdarzeń: {len(events)}",
        "",
    ]

    for i, ev in enumerate(events):
        level_icon = "[ERROR]" if ev.get("Level") == "Error" else "[WARN]"
        lines.append(f"{level_icon} {ev.get('SourceName', '?')} | EventID: {ev.get('EventID', '?')}")
        lines.append(f"  {ev.get('Message', '')[:200]}")

        r = results[i] if i < len(results) else None
        if isinstance(r, dict) and "error" not in r:
            lines.append(f"  Analiza:")
            lines.append(f"  - Co to jest: {r.get('explanation', '')}")
            lines.append(f"  - Czy to powazne: {r.get('severity', '')}")
            lines.append(f"  - Co zrobic: {r.get('steps', '')}")
            if r.get("tip"):
                lines.append(f"  - Wskazowka: {r.get('tip', '')}")
        elif isinstance(r, str):
            lines.append(f"  Blad: {r}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_html(path: str, results: list, events: list[dict]):
    """Export analysis results to a dark-themed HTML report.

    Args:
        path: Output file path.
        results: List of analysis result dicts (or error strings).
        events: List of event dicts corresponding to results.
    """
    rows_html = ""
    for i, ev in enumerate(events):
        level_color = "#E74C3C" if ev.get("Level") == "Error" else "#F39C12"
        analysis_html = ""
        r = results[i] if i < len(results) else None
        if isinstance(r, dict) and "error" not in r:
            analysis_html = (
                f'<div class="analysis">'
                f'<p><strong>Co to jest:</strong> {_escape(r.get("explanation", ""))}</p>'
                f'<p><strong>Czy to powazne:</strong> {_escape(r.get("severity", ""))}</p>'
                f'<p><strong>Co zrobic:</strong> {_escape(r.get("steps", ""))}</p>'
            )
            if r.get("tip"):
                analysis_html += f'<p><strong>Wskazowka:</strong> {_escape(r.get("tip", ""))}</p>'
            analysis_html += "</div>"
        elif isinstance(r, str):
            analysis_html = f'<div class="analysis"><p class="error">Blad: {_escape(r)}</p></div>'

        rows_html += f"""<tr>
<td style="color:{level_color}">{_escape(ev.get("Level", ""))}</td>
<td>{_escape(ev.get("SourceName", ""))}</td>
<td>{ev.get("EventID", "")}</td>
<td>{_escape(ev.get("Message", "")[:200])}</td>
<td>{analysis_html}</td>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>WinLog Analyzer - Raport</title>
<style>
body {{ background: #1A1A2E; color: #ECF0F1; font-family: Segoe UI, sans-serif; padding: 20px; }}
h1 {{ color: #3D5A80; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ border: 1px solid #2C3E50; padding: 10px; text-align: left; vertical-align: top; }}
th {{ background: #16213E; color: #3D5A80; }}
.analysis {{ background: #16213E; padding: 8px; border-radius: 4px; margin-top: 4px; }}
.analysis p {{ margin: 4px 0; }}
.error {{ color: #E74C3C; }}
</style>
</head>
<body>
<h1>WinLog Analyzer - Raport</h1>
<p>Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<p>Liczba zdarzen: {len(events)}</p>
<table>
<thead><tr><th>Poziom</th><th>Zrodlo</th><th>Event ID</th><th>Opis</th><th>Analiza AI</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _escape(text: str) -> str:
    """Escape HTML special characters for safe embedding."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
