# simple-inventory
Rudimentäres Inventursystem

Eine minimalistische, Docker-basierte Inventarverwaltung für Kisten, Fächer & Schubladen.

Per NFC-Aufkleber mit URL zur Box bespielen und direkt draufkleben und ganz einfach vom Handy oder PC bearbeiten. 

<img width="527" height="658" alt="image" src="https://github.com/user-attachments/assets/f36816e2-771b-4e2d-8c4d-1cf3f691a347" />
<img width="483" height="321" alt="image" src="https://github.com/user-attachments/assets/8f5610e9-639f-4975-ac96-a685c4460ddf" />

# TODO
Beschreibung, Dokumentation, Testen


# Schnellstart
```git clone https://github.com/moritzc/simple-inventory```

```cd simple-inventory/```

```docker compose up --build```

Die Weboberfläche ist via http://localhost:8088 erreichbar.

Boxen können statisch über ihre ID verlinkt werden. Beispielsweise http://localhost:8088/box/1
