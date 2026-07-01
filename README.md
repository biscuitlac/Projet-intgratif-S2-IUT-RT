# 🛡️ HomeGuard — Passerelle DNS intelligente

> **SAÉ 24 — Projet Intégratif** · BUT R&T 1ère année · IUT Nancy-Brabois  
> Filtrage DNS par intelligence artificielle avec tableau de bord Green ICT

---

## Présentation

HomeGuard est une passerelle DNS intelligente qui s'intègre avec **AdGuard Home** pour détecter et bloquer automatiquement des domaines publicitaires, traceurs et malveillants, grâce à un classifieur **Random Forest** entraîné sur les caractéristiques structurelles des noms de domaine.

Le projet est composé de trois parties :

- **API FastAPI** — passerelle entre le dashboard et l'API AdGuard Home
- **Classifieur IA** — modèle Random Forest qui analyse les requêtes DNS en temps réel
- **Dashboard web** — trois pages de visualisation (Vue d'ensemble, Détection IA, Impact Écologique)

---

## Architecture

```
HomeGuard/
│
├── Backend Python
│   ├── main.py              # API FastAPI (passerelle AdGuard Home)
│   ├── autorun.py           # Lancement automatique avec uvicorn
│   ├── config.py            # Configuration (à partir des variables d'env)
│   ├── classifier.py        # Boucle de détection IA (mode production)
│   ├── classifier_demo.py   # Boucle de détection IA (mode démo vidéo)
│   └── train.py             # Entraînement du modèle Random Forest
│
├── Modèle IA
│   ├── model.pkl            # Modèle entraîné (généré par train.py, non versionné)
│   ├── ai_blocks.json       # Log des domaines bloqués par l'IA
│   ├── classifier.py        # Boucle de détection IA (mode production)
│   ├── classifier_demo.py   # Boucle de détection IA (mode démo vidéo)
│   └── train.py             # Entraînement du modèle Random Forest
│
└── Dashboard HTML/JS/CSS
    ├── stats de base.html   # Vue d'ensemble DNS
    ├── stats_base.js
    ├── IA.html              # Page détection IA
    ├── IA.js
    ├── environnement.html   # Impact écologique
    ├── environnement.js
    └── project integratif.css
```

---

## Prérequis

- Python 3.10+
- AdGuard Home installé et accessible sur le réseau
- Fichiers d'entraînement : `ad_domains.txt` et `legit_domains.txt`

---

## Installation

```bash
git clone https://github.com/<votre-compte>/homeguard.git
cd homeguard
pip install -r requirements.txt
```

### Dépendances principales

```
fastapi
uvicorn
httpx
scikit-learn
pandas
joblib
requests
```

---

## Configuration

Les identifiants AdGuard Home ne doivent **jamais** être écrits en dur dans le code.  
Créez un fichier `.env` à la racine (il est ignoré par git) :

```env
ADGUARD_URL=http://10.66.88.1:80
ADGUARD_USER=votre_utilisateur
ADGUARD_PASSWORD=votre_mot_de_passe
```

`config.py` lit ces valeurs via `os.environ` :

```python
import os
ADGUARD_URL      = os.environ["ADGUARD_URL"]
ADGUARD_USER     = os.environ["ADGUARD_USER"]
ADGUARD_PASSWORD = os.environ["ADGUARD_PASSWORD"]
```

> ⚠️ **Ne jamais committer `config.py` avec des vraies valeurs, ni le fichier `.env`.**

---

## Utilisation

### 1. Entraîner le modèle

```bash
python train.py
# → génère model.pkl
```

### 2. Lancer l'API

```bash
python autorun.py
# ou directement :
uvicorn main:app --reload --port 8000
```

L'API est disponible sur `http://localhost:8000`.  
Documentation interactive : `http://localhost:8000/docs`

### 3. Lancer le classifieur IA

```bash
# Mode production (silencieux)
python classifier.py

# Mode démo (affichage coloré terminal)
python classifier_demo.py
```

### 4. Dashboard

Ouvrir `stats de base.html` dans un navigateur (le frontend appelle l'API sur le port 8000).

---

## Endpoints API principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/stats` | Statistiques globales AdGuard |
| GET | `/stats/summary` | Résumé rapide pour le dashboard |
| GET | `/stats/queried-by-category` | Requêtes DNS classées par catégorie |
| GET | `/stats/blocked-by-category` | Blocages classés par catégorie |
| GET | `/ia/stats` | KPIs du classifieur IA |
| GET | `/ia/blocks` | Liste des domaines bloqués par l'IA |
| GET | `/ia/blocks/recent` | Derniers domaines bloqués |
| GET | `/ia/vs-listes` | Comparaison IA vs listes classiques |
| GET | `/ia/scores/distribution` | Distribution des scores de confiance |
| GET | `/ia/environmental` | Impact environnemental estimé |
| GET | `/ia/evolution` | Évolution temporelle des blocages |

---

## Modèle IA

Le classifieur est un **Random Forest** (200 arbres, profondeur max 20) entraîné sur des caractéristiques structurelles des noms de domaine, sans résolution DNS ni lookup réseau.

**Features utilisées :**

| Feature | Description |
|---------|-------------|
| `length` | Longueur totale du domaine |
| `nb_subdomains` | Nombre de sous-domaines |
| `entropy` | Entropie de Shannon du SLD |
| `has_ad_keyword` | Présence de mots-clés pub/tracking |
| `digit_ratio` | Ratio de chiffres dans le SLD |
| `vowel_ratio` | Ratio de voyelles dans le SLD |
| `is_tld_new` | TLD de type "nouveau" (.xyz, .top…) |
| `longest_num_seq` | Plus longue séquence de chiffres |
| … | 18 features au total |

**Seuil de décision :** 0.85 (configurable dans `classifier.py`)

---

## Green ICT

Le dashboard mesure l'impact environnemental du filtrage DNS en estimant :

- **Données économisées** (Mo) — basé sur 2,05 Mo par domaine pub bloqué
- **Énergie économisée** (kWh) — 0,06 kWh/Go (IEA 2020)
- **CO₂ évité** (g) — 52 g CO₂/kWh (mix électrique français, RTE 2023)

---

## Fichiers exclus du dépôt (`.gitignore`)

```gitignore
# Secrets
.env
config.py

# Modèle entraîné (lourd, reproductible)
model.pkl

# Données d'entraînement
ad_domains.txt
legit_domains.txt

# Logs runtime
ai_blocks.json

# Python
__pycache__/
*.pyc
.venv/
```

---

## English summary

**HomeGuard** is an AI-powered DNS filtering gateway built on top of AdGuard Home.  
A Random Forest classifier analyses DNS queries in real time using structural domain features (entropy, length, digit ratio, ad keywords…) to detect and block advertising and tracking domains that evade traditional blocklists.

The project includes a FastAPI backend, a live-updating HTML dashboard (DNS overview, AI detections, ecological impact), and a Green ICT module that estimates CO₂ savings from blocked traffic.

---

## Équipe

Projet réalisé dans le cadre de la **SAÉ 24 — Projet Intégratif** du BUT Réseaux & Télécommunications,  
IUT Nancy-Brabois, Université de Lorraine.

---

## Licence

Usage académique — IUT Nancy-Brabois 2025-2026.
