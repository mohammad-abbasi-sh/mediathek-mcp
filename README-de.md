# mediathek-mcp 📺

**Die deutsche Mediathek** über die kostenlose [MediathekViewWeb](https://mediathekviewweb.de)-API — inoffizieller, **nur lesender** MCP-Server: Sendungen von ARD, ZDF, 3sat, ARTE, Phoenix, tagesschau24, KiKA und den Regionalsendern durchsuchen. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory“ (Sepehr-Stil). Keine Verbindung zu MediathekView, ARD oder ZDF.

## Für KI-Agenten

In die MCP-Konfiguration eintragen (stdio):

```json
{
  "mcpServers": {
    "mediathek": {
      "command": "uvx",
      "args": ["mediathek-mcp"]
    }
  }
}
```

Oder lokal starten: `python -m mediathek_mcp.server` (benötigt `mcp<2`, `httpx`).

## Werkzeuge

| Werkzeug | Beschreibung |
|------|-------------|
| `mediathek_search_programmes` | Sendungen nach Titel, Thema oder Beschreibung suchen — `query` (z. B. „Tagesschau“), optional `channel` (z. B. „ZDF“), `limit` 1..50 |
| `mediathek_latest_broadcasts` | Neueste Sendungen aller Sender, neueste zuerst — `limit` 1..50 |
| `mediathek_by_channel` | Neueste Sendungen eines Senders — `channel` (z. B. „ZDF“, „ARD“, „3sat“, „ARTE.DE“, „PHOENIX“), `limit` 1..50 |
| `mediathek_by_topic` | Alle Folgen einer Sendung/Serie — `topic` (z. B. „heute journal“), `limit` 1..50 |
| `mediathek_programme_detail` | Details einer Sendung: alle Video-URLs (niedrig/Standard/HD), Untertitel-URL, Webseiten-Link — `title` (exakt), optional `channel` |
| `mediathek_list_channels` | Sender der Filmliste (kuratierte Liste — die API hat keinen Senderlisten-Endpunkt) |

Hinweise:
- Die Filmliste enthält ca. 700.000 Sendungen und wird mehrmals täglich aktualisiert; die Ergebnisse sind neueste zuerst sortiert.
- „Neueste Sendungen“ sucht nach dem häufigsten Buchstaben in Titel/Thema/Beschreibung — die API liefert bei leerer Anfrage nichts und kennt keinen Platzhalter; das Ergebnis sind praktisch die neuesten Sendungen.
- Die Senderfilterung in `mediathek_search_programmes` erfolgt clientseitig über die neuesten 50 Texttreffer (die API kennt keine UND-Anfrage); `mediathek_by_channel` fragt den Sender direkt ab.
- `total_results` ist bei sehr breiten Anfragen von der API auf 10.000 begrenzt.
- Video-URLs sind direkte MP4-Links (niedrig / Standard / HD); `subtitle_url` ist leer, wenn keine Untertitel existieren.
- Daten: öffentliche MediathekViewWeb-API — kein Schlüssel, keine Anmeldung, nur lesend.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, mit echten aufgezeichneten API-Antworten (19 Tests)
- `tests/test_live.py` — wenige vorsichtige Live-Anfragen an mediathekviewweb.de (6 Tests)

Tests: 25/25 grün (19 offline + 6 live, 09.11.2026).

## Lizenz

MIT
