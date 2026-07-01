"""
API Python — Passerelle AdGuard Home
Démarre avec : uvicorn main:app --reload --port 8000
"""

import time
import json
import os
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import base64
from typing import Optional
from config import ADGUARD_URL, ADGUARD_USER, ADGUARD_PASSWORD

# Chemin vers le fichier de logs de l'IA
AI_BLOCKS_FILE = "/root/ai_dns/ai_blocks.json"

app = FastAPI(
    title="AdGuard Home API Gateway",
    description="Passerelle JSON pour votre tableau de bord",
    version="1.0.0",
)

# CORS — autoriser votre tableau de bord HTML à appeler cette API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Remplacer par l'URL de votre dashboard en production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def auth_header() -> dict:
    """Génère le header Basic Auth pour AdGuard Home."""
    credentials = base64.b64encode(f"{ADGUARD_USER}:{ADGUARD_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


async def adguard_get(path: str) -> dict:
    """Appel GET vers l'API AdGuard Home."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ADGUARD_URL}/control/{path}",
                headers=auth_header(),
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Impossible de joindre AdGuard Home")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))


async def adguard_post(path: str, payload: dict = {}) -> dict:
    """Appel POST vers l'API AdGuard Home."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ADGUARD_URL}/control/{path}",
                headers={**auth_header(), "Content-Type": "application/json"},
                json=payload,
                timeout=5.0,
            )
            response.raise_for_status()
            # Certains endpoints retournent un body vide
            return response.json() if response.content else {"success": True}
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Impossible de joindre AdGuard Home")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))


# ─────────────────────────────────────────────
# STATUT & INFOS GÉNÉRALES
# ─────────────────────────────────────────────

@app.get("/status", summary="Statut général d'AdGuard Home")
async def get_status():
    """Retourne l'état du serveur, version, protection activée ou non."""
    return await adguard_get("status")


@app.get("/stats", summary="Statistiques globales")
async def get_stats():
    """
    Retourne :
    - num_dns_queries : total requêtes DNS
    - num_blocked_filtering : requêtes bloquées
    - num_replaced_safebrowsing : sites malveillants bloqués
    - top_queried_domains : top domaines demandés
    - top_blocked_domains : top domaines bloqués
    - top_clients : top appareils
    """
    return await adguard_get("stats")


@app.get("/stats/summary", summary="Résumé rapide pour le dashboard")
async def get_stats_summary():
    """Version condensée des stats — idéale pour les widgets du dashboard."""
    data = await adguard_get("stats")
    total = data.get("num_dns_queries", 0)
    blocked = data.get("num_blocked_filtering", 0)
    return {
        "total_queries": total,
        "blocked_queries": blocked,
        "blocked_percent": round(blocked / total * 100, 1) if total else 0,
        "top_blocked_domains": data.get("top_blocked_domains", [])[:5],
        "top_clients": data.get("top_clients", [])[:5],
    }


@app.get("/stats/history", summary="Historique des requêtes dans le temps")
async def get_stats_history():
    """Données temporelles pour générer un graphique (intervalles de 30 min)."""
    data = await adguard_get("stats")
    return {
        "dns_queries": data.get("dns_queries", []),
        "blocked_filtering": data.get("blocked_filtering", []),
    }


# ─────────────────────────────────────────────
# JOURNAL DES REQUÊTES
# ─────────────────────────────────────────────

@app.get("/querylog", summary="Journal des requêtes DNS")
async def get_querylog(
    limit: int = Query(default=50, le=1000, description="Nombre de résultats"),
    offset: int = Query(default=0, description="Décalage pour la pagination"),
    search: Optional[str] = Query(default=None, description="Filtrer par domaine"),
    status: Optional[str] = Query(default=None, description="filtered | processed | all"),
):
    """Journal des requêtes DNS avec pagination et filtres."""
    params = f"older_than=&offset={offset}&limit={limit}"
    if search:
        params += f"&search={search}"
    if status:
        params += f"&response_status={status}"
    return await adguard_get(f"querylog?{params}")


# ─────────────────────────────────────────────
# FILTRAGE & LISTES
# ─────────────────────────────────────────────

@app.get("/filtering", summary="État du filtrage et listes de blocage")
async def get_filtering():
    """Retourne si le filtrage est actif et la liste des blocklists configurées."""
    return await adguard_get("filtering/status")


@app.post("/filtering/enable", summary="Activer le filtrage")
async def enable_filtering():
    """Active le blocage des publicités et trackers."""
    return await adguard_post("filtering/config", {"enabled": True, "interval": 24})


@app.post("/filtering/disable", summary="Désactiver le filtrage")
async def disable_filtering():
    """Désactive temporairement le blocage."""
    return await adguard_post("filtering/config", {"enabled": False, "interval": 24})


# ─────────────────────────────────────────────
# CLIENTS (APPAREILS)
# ─────────────────────────────────────────────

@app.get("/clients", summary="Liste des appareils connus")
async def get_clients():
    """Retourne tous les clients (appareils) configurés dans AdGuard Home."""
    return await adguard_get("clients")


# ─────────────────────────────────────────────
# LISTES PERSONNALISÉES (whitelist / blacklist)
# ─────────────────────────────────────────────

async def get_user_rules() -> list[str]:
    """Récupère la liste actuelle des règles custom depuis AdGuard Home."""
    data = await adguard_get("filtering/status")
    return data.get("user_rules", [])


async def set_user_rules(rules: list[str]) -> dict:
    """Remplace l'intégralité des règles custom sur AdGuard Home.

    L'API AdGuard Home ne propose pas d'ajout incrémental : POST /filtering/set_rules
    remplace toute la liste, donc il faut toujours envoyer le set complet désiré.
    """
    return await adguard_post("filtering/set_rules", {"rules": rules})


@app.get("/rules/custom", summary="Règles de filtrage personnalisées")
async def get_custom_rules():
    """Retourne les règles custom (domaines bloqués/autorisés manuellement)."""
    return {"rules": await get_user_rules()}


@app.post("/rules/block", summary="Bloquer un domaine")
async def block_domain(domain: str = Query(..., description="Domaine à bloquer, ex: ads.example.com")):
    """Ajoute un domaine à la liste noire personnalisée."""
    rule = f"||{domain}^"
    rules = await get_user_rules()
    if rule not in rules:
        rules.append(rule)
    await set_user_rules(rules)
    return {"success": True, "rule": rule}


@app.post("/rules/allow", summary="Autoriser un domaine")
async def allow_domain(domain: str = Query(..., description="Domaine à autoriser, ex: example.com")):
    """Ajoute un domaine à la liste blanche personnalisée."""
    rule = f"@@||{domain}^"
    rules = await get_user_rules()
    if rule not in rules:
        rules.append(rule)
    await set_user_rules(rules)
    return {"success": True, "rule": rule}


# ─────────────────────────────────────────────
# CLASSIFICATION DES DOMAINES BLOQUÉS
# ─────────────────────────────────────────────

# Règles de classification par mots-clés (ordre = priorité)
DOMAIN_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Publicité", [
        "ads", "ad", "doubleclick", "adservice", "advertising", "banner",
        "adnxs", "googlesyndication", "adtech", "adform", "adroll",
        "criteo", "taboola", "outbrain", "pubmatic", "rubiconproject",
    ]),
    ("Tracking & Analytics", [
        "track", "tracker", "analytics", "telemetry", "metrics",
        "pixel", "beacon", "stats", "collect", "log", "segment",
        "hotjar", "mixpanel", "amplitude", "heap", "fullstory",
        "newrelic", "datadog", "sentry",
    ]),
    ("Réseaux sociaux", [
        "facebook", "instagram", "twitter", "tiktok", "snapchat",
        "linkedin", "pinterest", "reddit", "tumblr", "whatsapp",
    ]),
    ("Contenu adulte", [
        "porn", "xxx", "sex", "adult", "hentai", "erotic",
        "xvideos", "xhamster", "pornhub", "youporn", "redtube",
    ]),
    ("Malware & Phishing", [
        "malware", "phish", "virus", "trojan", "ransomware",
        "botnet", "exploit", "hack", "crack", "keygen",
    ]),
    ("Jeux & Paris", [
        "casino", "poker", "bet", "gambling", "lottery",
        "slots", "bingo", "sport-bet", "betting",
    ]),
    ("Streaming & Médias", [
        "stream", "video", "media", "cdn", "content",
        "netflix", "youtube", "twitch", "vimeo", "dailymotion",
    ]),
    ("Cryptomonnaie & Mining", [
        "crypto", "bitcoin", "mining", "miner", "coin",
        "wallet", "blockchain", "nft", "coinhive",
    ]),
]

CATEGORY_OTHER = "Autre"


def classify_domain(domain: str) -> str:
    """Retourne la catégorie d'un domaine selon ses mots-clés."""
    domain_lower = domain.lower()
    for category, keywords in DOMAIN_CATEGORIES:
        if any(kw in domain_lower for kw in keywords):
            return category
    return CATEGORY_OTHER


def extract_domain_from_rule(rule: str) -> str:
    """Extrait le nom de domaine depuis une règle AdGuard (ex: ||ads.example.com^)."""
    return rule.strip().lstrip("|@").rstrip("^").lstrip("|")


async def fetch_avg_duration_by_domain(limit: int = 1000) -> dict[str, float]:
    """
    Interroge le querylog et retourne un dict { domain -> avg_elapsed_ms }
    calculé sur les `limit` dernières entrées.
    """
    data = await adguard_get(f"querylog?limit={limit}&offset=0")
    entries = data.get("data", [])

    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for entry in entries:
        domain = entry.get("question", {}).get("name", "").rstrip(".")
        elapsed = entry.get("elapsedMs")
        if domain and elapsed is not None:
            totals[domain] = totals.get(domain, 0.0) + float(elapsed)
            counts[domain] = counts.get(domain, 0) + 1

    return {
        domain: round(totals[domain] / counts[domain], 2)
        for domain in totals
    }


@app.get("/stats/blocked-by-category", summary="Domaines bloqués classés par catégorie")
async def get_blocked_by_category():
    """
    Récupère les top domaines bloqués depuis les stats et les règles custom,
    puis les classe par catégorie selon leurs mots-clés.

    Retourne :
    - categories : dict { catégorie -> liste de domaines avec count et duration_ms moyen }
    - summary : dict { catégorie -> nombre de domaines }
    - total : nombre total de domaines bloqués analysés
    """
    avg_duration = await fetch_avg_duration_by_domain()

    data = await adguard_get("stats")
    top_blocked: list[dict] = data.get("top_blocked_domains", [])

    # top_blocked_domains est une liste de dicts {domaine: count}
    domains_with_count: list[tuple[str, int]] = []
    for entry in top_blocked:
        for domain, count in entry.items():
            domains_with_count.append((domain, count))

    # Ajouter les règles custom bloquantes (||domain^)
    filtering_data = await adguard_get("filtering/status")
    for rule in filtering_data.get("user_rules", []):
        if rule.startswith("||") and rule.endswith("^"):
            domain = extract_domain_from_rule(rule)
            if domain and not any(d == domain for d, _ in domains_with_count):
                domains_with_count.append((domain, 0))

    # Classifier chaque domaine
    categories: dict[str, list[dict]] = {}
    for domain, count in domains_with_count:
        cat = classify_domain(domain)
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "domain": domain,
            "count": count,
            "duration_ms": avg_duration.get(domain),
        })

    # Trier chaque catégorie par nombre de requêtes bloquées décroissant
    for cat in categories:
        categories[cat].sort(key=lambda x: x["count"], reverse=True)

    summary = {cat: len(domains) for cat, domains in categories.items()}

    return {
        "total": len(domains_with_count),
        "summary": summary,
        "categories": categories,
    }


@app.get("/stats/queried-by-category", summary="Domaines demandés classés par catégorie")
async def get_queried_by_category():
    """
    Récupère les top domaines demandés (top_queried_domains) depuis les stats,
    puis les classe par catégorie selon leurs mots-clés.

    Retourne :
    - categories : dict { catégorie -> liste de domaines avec count et duration_ms moyen }
    - summary : dict { catégorie -> nombre de domaines }
    - total : nombre total de domaines demandés analysés
    """
    avg_duration = await fetch_avg_duration_by_domain()

    data = await adguard_get("stats")
    top_queried: list[dict] = data.get("top_queried_domains", [])

    # top_queried_domains est une liste de dicts {domaine: count}
    domains_with_count: list[tuple[str, int]] = []
    for entry in top_queried:
        for domain, count in entry.items():
            domains_with_count.append((domain, count))

    # Classifier chaque domaine
    categories: dict[str, list[dict]] = {}
    for domain, count in domains_with_count:
        cat = classify_domain(domain)
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "domain": domain,
            "count": count,
            "duration_ms": avg_duration.get(domain),
        })

    # Trier chaque catégorie par nombre de requêtes décroissant
    for cat in categories:
        categories[cat].sort(key=lambda x: x["count"], reverse=True)

    summary = {cat: len(domains) for cat, domains in categories.items()}

    return {
        "total": len(domains_with_count),
        "summary": summary,
        "categories": categories,
    }


# ─────────────────────────────────────────────
# DNS
# ─────────────────────────────────────────────

@app.get("/dns/config", summary="Configuration DNS upstream")
async def get_dns_config():
    """Retourne les serveurs DNS upstream configurés et les options de cache."""
    return await adguard_get("dns_info")


@app.get("/dns/check/{domain}", summary="Vérifier si un domaine est bloqué")
async def check_domain(domain: str):
    """Vérifie si un domaine spécifique serait bloqué par AdGuard Home."""
    return await adguard_get(f"filtering/check_host?name={domain}")


# ─────────────────────────────────────────────
# STATISTIQUES IA — Random Forest
# ─────────────────────────────────────────────

def load_ai_blocks() -> list[dict]:
    """Charge le fichier ai_blocks.json généré par classifier.py."""
    try:
        with open(AI_BLOCKS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


@app.get("/ia/stats", summary="Statistiques globales du modèle IA")
async def get_ia_stats():
    """
    Retourne les statistiques globales de l'IA :
    - total_bloques     : nombre total de domaines bloqués par l'IA
    - score_moyen       : score de confiance moyen du modèle
    - score_min         : score le plus bas ayant déclenché un blocage
    - score_max         : score le plus haut
    - premier_blocage   : date du premier blocage IA
    - dernier_blocage   : date du dernier blocage IA
    """
    logs = load_ai_blocks()
    if not logs:
        return {
            "total_bloques": 0,
            "score_moyen": None,
            "score_min": None,
            "score_max": None,
            "premier_blocage": None,
            "dernier_blocage": None,
        }

    scores = [entry["score"] for entry in logs]
    dates  = [entry["date"]  for entry in logs]

    return {
        "total_bloques":   len(logs),
        "score_moyen":     round(sum(scores) / len(scores), 3),
        "score_min":       round(min(scores), 3),
        "score_max":       round(max(scores), 3),
        "premier_blocage": min(dates),
        "dernier_blocage": max(dates),
    }


@app.get("/ia/blocks", summary="Liste des domaines bloqués par l'IA")
async def get_ia_blocks(
    limit: int = Query(default=50, le=500, description="Nombre de résultats"),
    offset: int = Query(default=0, description="Décalage pour la pagination"),
):
    """
    Retourne la liste paginée des domaines bloqués par le modèle IA,
    triée du plus récent au plus ancien.
    """
    logs = load_ai_blocks()
    logs_tries = sorted(logs, key=lambda x: x["date"], reverse=True)
    page = logs_tries[offset: offset + limit]

    return {
        "total":   len(logs),
        "offset":  offset,
        "limit":   limit,
        "results": page,
    }


@app.get("/ia/blocks/recent", summary="Derniers domaines bloqués par l'IA")
async def get_ia_blocks_recent(
    n: int = Query(default=10, le=100, description="Nombre de derniers blocages"),
):
    """Retourne les n derniers domaines bloqués par l'IA — idéal pour un widget dashboard."""
    logs = load_ai_blocks()
    logs_tries = sorted(logs, key=lambda x: x["date"], reverse=True)
    return {
        "total":   len(logs),
        "results": logs_tries[:n],
    }


@app.get("/ia/summary", summary="Résumé IA pour le dashboard")
async def get_ia_summary():
    """
    Version condensée combinant stats IA + stats AdGuard —
    idéale pour un widget unique dans le dashboard.

    Retourne :
    - ia_total_bloques     : domaines bloqués par l'IA seule
    - ia_score_moyen       : score moyen du modèle
    - ia_derniers_blocages : 5 derniers domaines bloqués par l'IA
    - adguard_total        : total requêtes DNS AdGuard
    - adguard_bloques      : total requêtes bloquées AdGuard
    - adguard_percent      : pourcentage bloqué par AdGuard
    """
    logs = load_ai_blocks()
    adguard_data = await adguard_get("stats")

    total_adguard  = adguard_data.get("num_dns_queries", 0)
    blocked_adguard = adguard_data.get("num_blocked_filtering", 0)

    scores = [e["score"] for e in logs] if logs else []
    logs_tries = sorted(logs, key=lambda x: x["date"], reverse=True)

    return {
        "ia_total_bloques":     len(logs),
        "ia_score_moyen":       round(sum(scores) / len(scores), 3) if scores else None,
        "ia_derniers_blocages": logs_tries[:5],
        "adguard_total":        total_adguard,
        "adguard_bloques":      blocked_adguard,
        "adguard_percent":      round(blocked_adguard / total_adguard * 100, 1) if total_adguard else 0,
    }


@app.get("/ia/scores/distribution", summary="Distribution des scores de confiance IA")
async def get_ia_scores_distribution():
    """
    Répartit les blocages IA en tranches de score —
    utile pour générer un graphique dans le dashboard.

    Retourne :
    - tranches : [
        { "tranche": "85-90%", "count": 12 },
        { "tranche": "90-95%", "count": 28 },
        { "tranche": "95-100%", "count": 47 },
      ]
    """
    logs = load_ai_blocks()
    tranches = {
        "85-90%":  0,
        "90-95%":  0,
        "95-100%": 0,
    }
    for entry in logs:
        s = entry["score"]
        if s < 0.90:
            tranches["85-90%"]  += 1
        elif s < 0.95:
            tranches["90-95%"]  += 1
        else:
            tranches["95-100%"] += 1

    return {
        "total":   len(logs),
        "tranches": [{"tranche": k, "count": v} for k, v in tranches.items()],
    }


# ─────────────────────────────────────────────
# COMPARAISON IA vs LISTES CLASSIQUES
# ─────────────────────────────────────────────

@app.get("/ia/vs-listes", summary="Comparaison IA vs listes de blocage classiques")
async def get_ia_vs_listes():
    """
    Compare le nombre de domaines bloqués par l'IA seule
    vs le nombre bloqué par les listes classiques AdGuard.

    Retourne :
    - adguard_bloques      : total bloqué par les listes classiques
    - ia_bloques           : total bloqué par l'IA seule (non dans les listes)
    - ia_contribution_pct  : part de l'IA dans le blocage total
    - total                : total combiné
    """
    logs         = load_ai_blocks()
    adguard_data = await adguard_get("stats")

    adguard_bloques = adguard_data.get("num_blocked_filtering", 0)
    ia_bloques      = len(logs)
    total           = adguard_bloques + ia_bloques

    return {
        "adguard_bloques":     adguard_bloques,
        "ia_bloques":          ia_bloques,
        "total":               total,
        "ia_contribution_pct": round(ia_bloques / total * 100, 2) if total else 0,
        "adguard_pct":         round(adguard_bloques / total * 100, 2) if total else 0,
    }


# ─────────────────────────────────────────────
# IMPACT ENVIRONNEMENTAL
# ─────────────────────────────────────────────

# Facteurs de conversion (sources académiques)
# 1 Go de données internet = 0.06 kWh (IEA 2020)
# 1 kWh en France         = 52g CO2   (RTE 2023)
# Taille moyenne d'un domaine pub bloqué = 2.05 Mo
KWH_PAR_GO        = 0.06
CO2_PAR_KWH_G     = 52
TAILLE_MOY_PUB_MO = 2.05

@app.get("/ia/environmental", summary="Impact environnemental du filtrage IA")
async def get_ia_environmental():
    """
    Estime l'impact environnemental des domaines bloqués par l'IA.
    Basé sur les facteurs de conversion IEA 2020 et RTE 2023.

    Retourne :
    - nb_domaines_bloques    : nombre de domaines bloqués par l'IA
    - donnees_economisees_mo : volume de données économisé en Mo
    - donnees_economisees_go : volume de données économisé en Go
    - energie_economisee_kwh : énergie économisée en kWh
    - co2_evite_grammes      : CO2 évité en grammes
    - co2_evite_kg           : CO2 évité en kilogrammes
    - equivalent_km_voiture  : équivalent en km parcourus en voiture (170g CO2/km)
    - sources                : références des facteurs de conversion utilisés
    """
    logs = load_ai_blocks()

    # Inclure aussi les blocages AdGuard classiques pour l'impact total
    adguard_data    = await adguard_get("stats")
    adguard_bloques = adguard_data.get("num_blocked_filtering", 0)
    ia_bloques      = len(logs)
    total_bloques   = adguard_bloques + ia_bloques

    def calcul_impact(nb):
        donnees_mo  = nb * TAILLE_MOY_PUB_MO
        donnees_go  = donnees_mo / 1024
        energie_kwh = donnees_go * KWH_PAR_GO
        co2_g       = energie_kwh * CO2_PAR_KWH_G
        return {
            "nb_domaines_bloques":    nb,
            "donnees_economisees_mo": round(donnees_mo, 2),
            "donnees_economisees_go": round(donnees_go, 4),
            "energie_economisee_kwh": round(energie_kwh, 6),
            "co2_evite_grammes":      round(co2_g, 3),
            "co2_evite_kg":           round(co2_g / 1000, 6),
            "equivalent_km_voiture":  round(co2_g / 170, 4),
        }

    return {
        "ia_seule":    calcul_impact(ia_bloques),
        "adguard":     calcul_impact(adguard_bloques),
        "total":       calcul_impact(total_bloques),
        "sources": {
            "energie": "IEA 2020 — 0.06 kWh/Go",
            "co2":     "RTE 2023 — 52g CO2/kWh (mix électrique français)",
            "taille":  "2.05 Mo par domaine publicitaire bloqué (estimation)",
        }
    }


# ─────────────────────────────────────────────
# ÉVOLUTION TEMPORELLE DES BLOCAGES IA
# ─────────────────────────────────────────────

@app.get("/ia/evolution", summary="Évolution temporelle des blocages IA")
async def get_ia_evolution():
    """
    Retourne l'évolution du nombre de domaines bloqués par l'IA
    jour par jour — utile pour générer un graphique de tendance.

    Retourne :
    - par_jour    : liste [ { date, count, cumul } ]
    - aujourd_hui : nombre de blocages du jour
    - cette_semaine : nombre de blocages sur les 7 derniers jours
    - total       : total cumulé
    """
    logs = load_ai_blocks()
    if not logs:
        return {
            "par_jour":      [],
            "aujourd_hui":   0,
            "cette_semaine": 0,
            "total":         0,
        }

    # Compter par jour
    from collections import defaultdict
    from datetime import datetime, timedelta, timezone

    comptage: dict[str, int] = defaultdict(int)
    for entry in logs:
        date_str = entry["date"][:10]  # garder YYYY-MM-DD
        comptage[date_str] += 1

    # Trier et calculer le cumul
    dates_triees = sorted(comptage.keys())
    cumul = 0
    par_jour = []
    for date in dates_triees:
        cumul += comptage[date]
        par_jour.append({
            "date":  date,
            "count": comptage[date],
            "cumul": cumul,
        })

    # Stats rapides
    aujourd_hui   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    il_y_a_7_jours = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    count_auj     = comptage.get(aujourd_hui, 0)
    count_semaine = sum(v for k, v in comptage.items() if k >= il_y_a_7_jours)

    return {
        "par_jour":      par_jour,
        "aujourd_hui":   count_auj,
        "cette_semaine": count_semaine,
        "total":         cumul,
    }
