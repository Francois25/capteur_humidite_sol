![Texte alternatif](/web/auto_water_sys.webp "description du bandeau")
# 🌿 Projet : Capteur d'Hygrométrie du Sol & Arrosage Automatique

Système basé sur un **ESP32**, utilisant **MicroPython**, un serveur **Picoweb**, et une interface web locale.

## 📋 Fonctionnalités principales

- Mesure de l'**hygrométrie du sol** (capteur capacitif analogique)
- Lecture de la **température** et de l'**humidité de l'air** (capteur DHT22)
- Détection du **besoin en arrosage** automatique
- **Arrosage automatique** ou **manuel** (via bouton ou via interface web)
- **Interface Web Responsive** pour :
  - Consulter l'humidité, la température
  - Forcer ou arrêter l'arrosage
  - Vérifier l'état du Wi-Fi
- Envoi d'un **e-mail automatique** si besoin d'arrosage (SMTP Gmail)
- **Indicateurs visuels** par LEDs sur la carte ESP32
- **Reconnexion automatique au Wi-Fi** en cas de coupure
- **Surveillance via bouton manuel** en plus du web

## 🛠 Technologies utilisées

- **ESP32** sous **MicroPython v1.24**
- **uasyncio** pour la gestion multitâches
- **Picoweb** pour le serveur HTTP léger
- **umail** pour l'envoi de mails
- **ADC / GPIO** pour la lecture des capteurs
- **uasyncio.sleep()** pour les temporisations non-bloquantes

## 📦 Structure du projet

├── boot.py # Initialisation de l'ESP32 (démarrage automatique) ├── main.py # Programme principal (arrosage + serveur web) ├── /lib/ # Librairies MicroPython : picoweb, umail, etc. ├── /web/ # Fichiers Web à servir │ ├── index.html # Interface web │ ├── style.css # Style CSS associé │ ├── serre_hq_redim.webp # Image d'arrière-plan (compressée) │ ├── goutte_ico.png # Icône du site ├── wificonfig.py # Fichier avec identifiants Wi-Fi & SMTP ├── mailing_config.py # Fichier avec paramètres d'envoi de mail ├── README.md # Ce fichier

## ⚙️ Comment utiliser

1. **Flasher MicroPython** sur l'ESP32 si nécessaire
2. **Uploader tous les fichiers** vers l'ESP32 (via Thonny ou ampy)
3. Modifier :
   - `wificonfig.py` ➔ Ajouter vos identifiants Wi-Fi et SMTP
   - `mailing_config.py` ➔ Ajouter votre adresse email de destination
4. **Redémarrer l'ESP32** ➔ Lancement automatique du projet
5. Se connecter à l'adresse IP affichée dans le terminal (ex : `http://192.168.1.89`)

## 🚨 Points d'attention

- Bien compresser les images pour éviter l'erreur `Memory allocation failed`.
- Adapter les GPIOs si vos branchements sont différents.
- En cas de perte Wi-Fi, la LED clignote automatiquement jusqu'à reconnexion.
- Sur microPython, `sendfile()` Picoweb a été remplacé par `open()` pour la compatibilité.

## 📸 Interface web (Aperçu)

- Visualisation hygrométrie du sol 🌱
- Visualisation humidité/air et température 🌡️
- Switch d'arrosage (ON/OFF) ✅❌
- Indicateur Wi-Fi
- Fond d'écran personnalisé

## 📚 Remerciements

Projet développé avec ❤️ par **Parola François** - *Effpe Design*.

---
