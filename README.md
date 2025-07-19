# simple-inventory
Rudimentäres Inventursystem

Eine minimalistische, Docker-basierte Inventarverwaltung für Kisten, Fächer & Schubladen.

Per NFC-Aufkleber mit URL zur Box bespielen und direkt draufkleben und ganz einfach vom Handy oder PC bearbeiten. 

# TODO
- Suchfunktion
- Import-Export

# Schnellstart
```git clone https://github.com/moritzc/simple-inventory```

```cd simple-inventory/```

```docker compose up --build```

Die Weboberfläche ist via http://localhost:8000/static/index.html erreichbar.

Boxen können statisch über ihre ID verlinkt werden. Beispielsweise http://localhost:8000/static/index.html#box/4
