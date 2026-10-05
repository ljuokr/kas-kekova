# Kaş–Kekova Paddelkarte

Offline-Karte für eine viertägige Seekajak-Rundtour, 5.–8. Oktober 2026.
Die Seite zeigt vier Tagesetappen, zwei Routenvarianten, Ortsinformationen mit
Quellen und direkte GPX-/KML-Downloads ohne Google-Drive-Anmeldung.

| Variante | Mo | Di | Mi | Do | Gesamt |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mit Gökkaya-Ausflug | 22,5 km | 16,8 km | 26,6 km | 22,5 km | 88,5 km |
| Wende bei Kaleköy | 22,5 km | 16,8 km | 16,8 km | 22,5 km | 78,7 km |

Übernachtungsvorschlag: Aperlai, Kaleköy, Aperlai; alle Plätze und Anlandungen
vorher bestätigen. Die Andriake-Verlängerung ist ein separater Export mit rund
5,0 km einfacher Strecke ab Gökkaya und gehört nicht zur Rundtour.

## Dateien und Aktualisierung

- `index.html`: Oberfläche, eingebettete OSM-Küstenlinie, Ortsdetails und Quellen.
- `route-source.json`: ursprüngliche Wasserlinie, Anker, Wegpunkte und Tagespläne.
- `scripts/generate-routes.py`: erzeugt aus dieser Quelle `route-data.json` und
  alle sechs GPX-/KML-Dateien. Python 3.9+, keine zusätzlichen Pakete.
- `Kas-Kekova_Woche.gpx` / `.kml`: Rundtour mit Gökkaya, vier Tagestracks.
- `Kas-Kekova_ohne-Goekkaya.gpx` / `.kml`: Rundtour ohne Gökkaya.
- `Goekkaya-Andriake_Option.gpx` / `.kml`: separate Einwegverlängerung.
- `sw.js`: Offline-Cache für Karte, Daten und alle Downloads.

Nach Änderungen an den Routendaten:

```sh
python3 scripts/generate-routes.py
python3 scripts/generate-routes.py --check
```

Die Entfernungen werden auf dem WGS84-Ellipsoid zwischen aufeinanderfolgenden
Trackpunkten berechnet. Rundtouren beginnen und enden am selben Punkt. Die
vorhandene Wasserlinie wurde nur in Tagesetappen aufgeteilt und für die Rückfahrt
umgekehrt; es wurden keine neuen Abkürzungen eingezeichnet. Marker und tatsächliche
Anlandestellen sind nicht identisch. Die OSM-Geometrieprüfung ist keine nautische
Freigabe; die längste einzelne Gerade misst rund 9,5 km.

## Lokal prüfen

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

`http://127.0.0.1:8765/` öffnen. Varianten, Tagesauswahl, Ortsfilter, Zoom und
Downloads prüfen. Danach Server stoppen und Seite erneut laden, um den
Offline-Fallback zu kontrollieren. Service Worker benötigen HTTPS oder localhost.

Bei Änderungen an Cache-Dateien die Version in `sw.js` erhöhen und neue Dateien
in `FILES` ergänzen. Erst «Für offline gespeichert» bestätigt den vollständigen
Cache; vor der Reise auf dem Zielgerät im Flugmodus testen. Externe Karten und
Quellen bleiben nur mit Netz erreichbar.

## Quellen und Grenzen

Inhaltlicher Prüfstand: 5. Oktober 2026. Quellen stehen direkt bei den Orten.
Bewertungszahlen, unbestätigte Öffnungszeiten und pauschale Wildcamp-Erlaubnisse
wurden entfernt. Die rote Markierung ist ein schematischer Ruinenhinweis und keine
verifizierte amtliche Verbotsgrenze. Die Waldsperren Antalya 2026 gelten für Wald,
nicht pauschal für jeden Strand. Übernachtungen, lokale Regeln, Kajakübergabe und
Seewetter vor Ort abstimmen.

Küstenlinie © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright).
