<img src="custom_components/fritzbox_thermostat_presets/brand/icon.png" alt="" width="96" align="right">

# Thermostat Presets for Fritzbox

[![In Home Assistant öffnen und dieses Repository in HACS anzeigen.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tombrain&repository=fritzbox-thermostat-presets&category=integration)

🇬🇧 [English documentation](README.md)

Eine Home-Assistant-Integration, mit der du die **Komforttemperatur** und die
**Absenktemperatur** deiner FRITZ!DECT-Heizkörperregler an der Fritzbox ändern kannst.

Die mitgelieferte AVM-FRITZ!SmartHome-Integration kann nur die aktuelle Solltemperatur setzen.
Komfort- und Absenktemperatur, die der Zeitplan des Thermostats verwendet, lassen sich sonst
nur in der Fritzbox-Oberfläche ändern. Diese Integration stellt sie als Entitäten bereit, damit
du sie in Dashboards, Skripten und Automationen nutzen kannst.

> **Hinweis:** Dies ist ein unabhängiges Community-Projekt. Es steht in keiner Verbindung zu
> AVM / FRITZ! und wird von dort weder unterstützt noch empfohlen. FRITZ!, FRITZ!Box und
> FRITZ!DECT sind Marken der jeweiligen Inhaber.

## Funktionen

- Zwei Entitäten pro Thermostat: **Komforttemperatur** und **Absenktemperatur**
  (8–28 °C, 0,5-°C-Schritte)
- Nutzt die offizielle, dokumentierte
  [FRITZ! Smart Home REST-API](https://fritz.support/resources/SmarthomeRestApiFRITZOS82.html)
- Einrichtung über die Oberfläche, kein YAML nötig
- Lokale Abfrage alle 60 Sekunden, keine Cloud
- Erneute Anmeldung, wenn sich das Passwort ändert
- Diagnosedaten für Fehlerberichte
- Deutsch und Englisch

## Voraussetzungen

| | |
|---|---|
| Fritzbox | FRITZ!OS **8.20** oder neuer |
| Thermostate | FRITZ!DECT 301 (getestet); 302 und andere Thermostate, die die REST-API kennt, sollten funktionieren |
| Home Assistant | 2025.3 oder neuer |
| Fritzbox-Benutzer | Rechte **Smart Home** und **FRITZ!Box Einstellungen** |

### Fritzbox-Benutzer anlegen

1. Fritzbox-Oberfläche öffnen (http://fritz.box).
2. **System → FRITZ!Box-Benutzer → Benutzer hinzufügen**.
3. Namen wählen (z. B. `homeassistant`) und ein sicheres Passwort vergeben.
4. Die Rechte **Smart Home** und **FRITZ!Box Einstellungen** aktivieren.
   Das zweite Recht verlangt die REST-API zum *Ändern* von Thermostat-Einstellungen.
   Zum Lesen reicht **Smart Home**.
5. Übernehmen.

## Installation

### Über HACS (empfohlen)

1. In HACS das Menü (⋮) → **Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/tombrain/fritzbox-thermostat-presets` mit dem Typ **Integration** hinzufügen.
3. Nach **Thermostat Presets for Fritzbox** suchen und herunterladen.
4. Home Assistant neu starten.

### Manuell

1. Den Ordner `custom_components/fritzbox_thermostat_presets` in den Ordner
   `custom_components` deiner Home-Assistant-Konfiguration kopieren.
   Bei Home Assistant OS geht das z. B. mit dem Samba- oder File-Editor-Add-on.
2. Home Assistant neu starten.

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. Nach **Thermostat Presets for Fritzbox** suchen.
3. Eingeben:
   - **Host**: `fritz.box` oder die IP-Adresse deiner Fritzbox
   - **Benutzername** und **Passwort** des oben angelegten Fritzbox-Benutzers

Jedes Thermostat erscheint als Gerät mit zwei Entitäten im Bereich **Konfiguration**.

## Verwendung

### Entitäten

| Entität | Bedeutung |
|---|---|
| `number.<thermostat>_komforttemperatur` | Komforttemperatur (Heizzeiten im Zeitplan) |
| `number.<thermostat>_absenktemperatur` | Absenktemperatur (Absenkzeiten im Zeitplan) |

Die Entitäts-IDs hängen vom Namen des Thermostats und von der Sprache ab, die Home Assistant
bei der Einrichtung hatte. Mit englischer Oberfläche heißen sie z. B.
`number.wohnzimmer_comfort_temperature`.

### Dashboard-Karte

```yaml
type: entities
title: Heizung Wohnzimmer
entities:
  - entity: number.wohnzimmer_komforttemperatur
  - entity: number.wohnzimmer_absenktemperatur
```

### Aktion

```yaml
action: number.set_value
target:
  entity_id: number.wohnzimmer_komforttemperatur
data:
  value: 21.5
```

### Beispiel-Automation: Komfort an kalten Tagen erhöhen

```yaml
automation:
  - alias: "Komforttemperatur bei Frost erhöhen"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.aussentemperatur
        below: 0
    actions:
      - action: number.set_value
        target:
          entity_id: number.wohnzimmer_komforttemperatur
        data:
          value: 22.5

  - alias: "Komforttemperatur normal"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.aussentemperatur
        above: 3
    actions:
      - action: number.set_value
        target:
          entity_id: number.wohnzimmer_komforttemperatur
        data:
          value: 21.5
```

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| *Anmeldung fehlgeschlagen oder fehlende Benutzerrechte* bei der Einrichtung | Benutzername und Passwort prüfen. Der Benutzer braucht das Recht **Smart Home**. |
| *Verbindung fehlgeschlagen* | Host prüfen, statt `fritz.box` die IP-Adresse versuchen. FRITZ!OS muss 8.20 oder neuer sein, ältere Versionen haben die REST-API nicht. |
| *Zugriff verweigert … benötigt das Recht 'FRITZ!Box Einstellungen'* beim Ändern | Dem Fritzbox-Benutzer das Recht **FRITZ!Box Einstellungen** geben. |
| Ändern eines Werts schlägt fehl | Ist für das Thermostat in der Fritzbox eine **Temperaturgrenze** eingestellt, werden Werte außerhalb davon möglicherweise abgelehnt. |
| Wert in Home Assistant geändert, aber das Thermostat-Display zeigt noch den alten | Die Fritzbox überträgt den neuen Wert beim nächsten Funkkontakt des Thermostats; das kann einige Minuten dauern. |
| Thermostat erscheint doppelt | Diese Integration legt eigene Geräte an, getrennt von der AVM-FRITZ!SmartHome-Integration. |

### Debug-Protokoll

In der `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.fritzbox_thermostat_presets: debug
```

### Diagnosedaten

**Einstellungen → Geräte & Dienste → Thermostat Presets for Fritzbox → ⋮ → Diagnosedaten herunterladen.**
Benutzername und Passwort werden entfernt. Bitte diese Datei an Fehlerberichte anhängen.

## Lizenz

[MIT](LICENSE)
