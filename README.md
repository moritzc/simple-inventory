# simple-inventory
Rudimentäres Inventursystem

Eine minimalistische, Docker-basierte Inventarverwaltung für Kisten, Fächer & Schubladen.

Per NFC-Aufkleber mit URL zur Box bespielen und direkt draufkleben und ganz einfach vom Handy oder PC bearbeiten. 

# Index/Übersicht
<img width="766" height="375" alt="image" src="https://github.com/user-attachments/assets/1a103819-80fc-4c8e-b5ee-c4ebdb941ac7" />

# Übersicht einer Box
<img width="815" height="732" alt="image" src="https://github.com/user-attachments/assets/4eced54a-4bf2-49ab-989b-9be0359992ae" />

# Suchfunktion
<img width="342" height="383" alt="image" src="https://github.com/user-attachments/assets/5e2c5def-7886-4b74-b043-3744c52c8668" />


# Schnellstart
```git clone https://github.com/moritzc/simple-inventory```

```cd simple-inventory/```

```docker compose up --build```

Die Weboberfläche ist via http://localhost:8088 erreichbar.

Boxen können statisch über ihre ID verlinkt werden. Beispielsweise http://localhost:8088/box/1
