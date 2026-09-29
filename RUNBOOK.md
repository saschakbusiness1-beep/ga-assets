# Runbook @gesundheitsakte

Diese Datei ist die Arbeitsanweisung für die automatischen Läufe. Jeder Lauf startet in einer
**frischen Sitzung ohne Gedächtnis** — hier steht alles, was gebraucht wird.

Asset-Repo (alles liegt hier, lesbar ohne Anmeldung):
`https://raw.githubusercontent.com/saschakbusiness1-beep/ga-assets/main/`

| Datei | Inhalt |
|---|---|
| `plan_data.py` | `POSTS` — der 30-Tage-Plan mit Hook, Slides, Caption je Akte |
| `ga_render.py` | Renderer (PIL). Karussells, Einzelbilder, Reels, Musik |
| `Anton-Regular.ttf`, `PlusJakartaSans.ttf` | Schriften, lädt `ga_render` selbst nach |
| `bett-{demons,piano,neon,reality}.m4a` | Musikbetten, 35 s, -15 LUFS |
| `state.json` | Was zuletzt lief und was heute Abend bereitliegt |

---

## Die eiserne Regel: wer darf wohin schreiben

| | lesen | ins Repo schreiben | Higgsfield-CDN |
|---|---|---|---|
| Cloud-Container (`Bash`) | ja | **nein** | **nein** (Proxy sperrt) |
| Composio-Sandbox (`COMPOSIO_REMOTE_WORKBENCH`) | ja | ja | ja |

**Daraus folgt: alles, was veröffentlicht wird, entsteht in der Sandbox.** Der Container darf
Ergebnisse nur nachprüfen, indem er sie von `raw.githubusercontent.com` zurückholt.

Ins Repo schreiben geht so (in der Sandbox):

```python
run_composio_tool("GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS", {
    "owner":"saschakbusiness1-beep", "repo":"ga-assets",
    "path":"akte012/01.jpg", "message":"Akte 012",
    "content": base64.b64encode(open(p,"rb").read()).decode(), "branch":"main"})
```

Zum Überschreiben einer vorhandenen Datei muss `sha` mitgegeben werden — einfacher ist ein
**neuer Dateiname**. `raw.githubusercontent.com` cacht ohnehin; eine überschriebene Datei liefert
noch die alten Bytes zurück, Query-Parameter helfen nicht.

---

## Lauf A — morgens: bauen und prüfen

1. **Stand holen.** `state.json` lesen. `naechste` sagt, welche Akte dran ist.
   Gegenprüfen mit `INSTAGRAM_GET_IG_USER_MEDIA` (`account="gesundheitsakte"`, `limit=5`):
   Wenn der letzte Beitrag von heute ist, wurde schon gepostet — dann abbrechen und melden.

2. **Akte holen.** `plan_data.POSTS` laden, den Eintrag mit `n == naechste` nehmen.
   Darin: `fmt` (A/B/C), `art`, `titel`, `hook`, `slides`, `caption`, `bild`.
   Ist `naechste > 30`, siehe **Nach Akte 030** unten.

3. **Bilder erzeugen** mit `mcp__Higgsfield__generate_image_batch`, Modell `nano_banana_pro`,
   `4:5` für Karussell und Einzelbild, `9:16` für Reels, `quality "1080p"`.
   **Job-IDs sofort in eine Datei schreiben.** Fester Prompt-Baustein:

   ```
   cinematic editorial photograph, deep navy blue and cool shadow tones,
   single soft light source from the side, subtle violet rim light,
   matte film grain, shallow depth of field, muted desaturated palette,
   no text, no logos, no visible faces, vertical composition,
   generous empty space in the lower third
   ```

   Bei 9:16 statt „lower third" → „middle and lower area".
   Format C (Objekt) braucht lesbaren Text **im Objekt** — dann `no text` streichen und die
   zwei Zeilen wörtlich in den Prompt schreiben. Umlaute gehen oft schief: zwei Varianten
   erzeugen und die bessere nehmen.

4. **In der Sandbox** herunterladen, graden, rendern, hochladen — alles in einem Rutsch:

   ```python
   # graden: Sättigung 0.72, Kontrast 1.06, 14 % Navy, Helligkeit 1.04
   # danach mittlere Helligkeit auf 40–50 ziehen (ImageStat), sonst brennt Papier aus
   import ga_render as R
   pfade = R.karussell(12, eintraege, "/tmp/a012")   # eintraege: [(bildpfad, slide-dict), ...]
   ```

   Slide-Arten: `cover`, `befund`, `payoff`, `cta`, `panel`, `erkenntnis`, `objekt`.
   Headlines tragen `<br>` als Zeilenumbruch, `sub`/`b`/`beleg` brechen selbst um.

5. **Prüfen.** Die fertigen Bilder aus dem Repo in den Container holen und **ansehen**
   (`Read`). Worauf achten: fehlende Umlaute im generierten Text, abgeschnittene Zeilen,
   ausgebranntes Papier, doppelte Bildmotive innerhalb einer Akte.
   Sieht etwas falsch aus: neu erzeugen, nicht durchwinken.

6. **`state.json` schreiben** mit dem, was heute Abend rausgeht:

   ```json
   {"naechste": 13, "letzter_post": "2026-09-29",
    "bereit": {"akte": 12, "typ": "karussell",
               "bilder": ["akte012/01.jpg", "akte012/02.jpg"],
               "caption": "..."}}
   ```

   `typ` ist `karussell`, `bild` oder `reel`. Bei `reel` steht in `bilder` genau eine MP4-URL.

7. **Sascha Bescheid geben**: erstes Bild als Datei in den Chat, eine Zeile was drin ist.

---

## Lauf B — 18:30: veröffentlichen

1. `state.json` lesen. Kein `bereit`-Block oder `bereit.akte` schon gepostet → melden, nichts tun.

2. **Konto prüfen.** `INSTAGRAM_GET_USER_INFO` mit `account="gesundheitsakte"`.
   Kommt nicht `username: gesundheitsakte` (ID `38799316196382323`) zurück: **abbrechen**.
   Es sind zwei Konten verbunden, das zweite ist `abnehmen_mit_sascha`.

3. **Caption zusammensetzen**: Text aus `bereit.caption`, dann eine Leerzeile, ein Gedankenstrich
   in eigener Zeile, dann `Bild- und Videomaterial KI-generiert.`, dann die Hashtags.
   Der Hinweis gehört ans **Ende** — oben zerschießt er den Hook, und Instagram zeigt vor dem
   „mehr" ohnehin nur rund 125 Zeichen.

4. **Posten.**

   Einzelbild:
   ```
   INSTAGRAM_POST_IG_USER_MEDIA         (ig_user_id "me", image_url, caption) → creation_id
   INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH (creation_id, max_wait_seconds 150)   → ig_media_id
   ```
   Reel: zusätzlich `media_type: "REELS"` und `video_url` statt `image_url`.
   Karussell: je Bild einen Container mit `is_carousel_item: true`, dann einen Eltern-Container
   `media_type: "CAROUSEL"` mit `children`, den veröffentlichen.

   **Bei jedem einzelnen Aufruf `account="gesundheitsakte"` mitgeben.** Ohne Kontoangabe bricht
   Composio mit Fehler 4300 ab — das ist die Sicherung, nicht der Fehler.

5. `INSTAGRAM_GET_IG_MEDIA` → Permalink. `state.json` fortschreiben: `bereit` auf `null`,
   `letzter_post` auf heute. Permalink an Sascha.

---

## Was nie passieren darf

- Auf `abnehmen_mit_sascha` posten. Vor jedem Veröffentlichen das Konto prüfen.
- Ohne KI-Hinweis posten.
- Zweimal am selben Tag posten. Erst die letzten Beiträge abfragen.
- Ein Bild veröffentlichen, das niemand angesehen hat.

## Grenzen der Sandbox (kosten sonst zwei Anläufe)

985 MB RAM, ein Kern, 180 Sekunden je Zelle.

- ffmpeg immer `-threads 1`. Mit 2 stirbt es mit Exit 137.
- `zoompan` über etwa 90 Bildern stirbt ebenfalls — `ga_render.reel_montage` zerlegt deshalb
  jeden Beat in Stücke unter 70 Bildern. Nicht „vereinfachen".
- Zwischenauflösung höchstens 1188×2112.
- Vor jedem Durchlauf `gc.collect()`.
- Composio-Upload bricht über etwa 3 MB mit HTTP 413 ab. Reels am Ende einmal mit
  `-crf 25 -preset faster` nachkodieren, dann rund 1 MB.

## Nach Akte 030

Der Plan endet bei 30. Danach neue Fälle nach demselben Regelwerk weiterschreiben —
es steht in den Projektdokumenten `gesundheitsakte-erzaehlregeln.md` und
`gesundheitsakte-marke.md`. Die drei Regeln in Kurzform:

- **Format A (Fall, 12 Slides):** Die Auflösung kommt frühestens auf Slide 6. Vorher nur
  Beobachtung und Ausschluss. Ein Mensch, ein konkreter Auslöser, eine Änderung.
- **Format B (Liste, 10 Slides):** Cover mit Versprechen, dann Paare „tu das / nicht das",
  **jedes Paar mit einem Beleg**, danach eine Erkenntnis-Slide, dann CTA. Keine blanke
  Aufzählung — die langweilt.
- **Format C (Objekt, Einzelbild):** Der Widerspruch steht **im Objekt selbst**. Kein Overlay,
  kein Zettel daneben, keine erfundenen Messwerte.

Weiter gilt: keine Zahl ohne Deckung, keine erfundenen Studien, keine Wortspiel-Paare ohne
Inhalt, kein Paar zweimal über verschiedene Akten hinweg, und die Besetzung abwechseln
(bisher zwei Drittel weiblich).
