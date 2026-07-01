# classifier_demo.py — version démo vidéo
import joblib, requests, pandas as pd, math, json, time, os
from collections import Counter
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
HG_BASE  = "http://10.66.88.1"
HG_USER  = "TOM"
HG_PASS  = "Hbu&@ddYbgX&0UeK3ZQ2UAfBr17qR"
SEUIL    = 0.85
LOG_FILE = "ai_blocks.json"

# ── Couleurs terminal ─────────────────────────────────────────────────────────
ROUGE  = "\033[91m"
VERT   = "\033[92m"
JAUNE  = "\033[93m"
BLEU   = "\033[94m"
VIOLET = "\033[95m"
CYAN   = "\033[96m"
GRIS   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def clear():
    os.system('clear')

def banner():
    print(f"{BLEU}{BOLD}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         PASSERELLE DNS INTELLIGENTE — IA ACTIVE          ║")
    print("║              Détection publicitaire en temps réel        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

def barre_score(score):
    filled = int(score * 20)
    empty  = 20 - filled
    if score > 0.85:
        couleur = ROUGE
    elif score > 0.5:
        couleur = JAUNE
    else:
        couleur = VERT
    return f"{couleur}{'█' * filled}{'░' * empty}{RESET} {score:.0%}"

# ── Features ──────────────────────────────────────────────────────────────────
def extract_features(domain):
    parts = domain.split('.')
    sld = parts[-2] if len(parts) >= 2 else domain
    tld = parts[-1] if len(parts) >= 1 else ''
    def entropy(s):
        if not s: return 0
        ct = Counter(s)
        return -sum((v/len(s))*math.log2(v/len(s)) for v in ct.values())
    vowels     = sum(ch in 'aeiou' for ch in sld.lower())
    consonants = sum(ch.isalpha() and ch not in 'aeiou' for ch in sld.lower())
    has_repeated = int(any(sld[i] == sld[i+1] == sld[i+2]
                       for i in range(len(sld)-2)))
    alpha_ratio = sum(ch.isalpha() for ch in sld) / max(len(sld), 1)
    longest_num = 0
    cur = 0
    for ch in sld:
        cur = cur + 1 if ch.isdigit() else 0
        longest_num = max(longest_num, cur)
    return {
        'length': len(domain), 'nb_subdomains': len(parts)-2,
        'nb_digits': sum(ch.isdigit() for ch in domain),
        'nb_hyphens': domain.count('-'),
        'has_ad_keyword': int(any(k in domain for k in
                            ['ad','ads','track','click','pixel','analytics',
                             'telemetry','beacon','stat','metrics','collect',
                             'spy','log','cdn'])),
        'entropy': entropy(sld),
        'digit_ratio': sum(ch.isdigit() for ch in sld)/max(len(sld),1),
        'sld_length': len(sld), 'vowel_ratio': vowels/max(len(sld),1),
        'consonant_ratio': consonants/max(len(sld),1),
        'nb_dots': domain.count('.'), 'tld_is_com': int(tld=='com'),
        'has_numbers': int(any(ch.isdigit() for ch in sld)),
        'alpha_ratio': alpha_ratio, 'has_repeated': has_repeated,
        'longest_num_seq': longest_num, 'tld_length': len(tld),
        'is_tld_new': int(tld in ['xyz','top','club','online',
                                   'site','web','info','biz']),
    }

def pourquoi_suspect(features, domain):
    raisons = []
    if features['has_ad_keyword']:
        raisons.append("mot-clé pub détecté")
    if features['nb_subdomains'] > 2:
        raisons.append(f"{features['nb_subdomains']} sous-domaines")
    if features['entropy'] > 3.5:
        raisons.append("nom aléatoire (entropie élevée)")
    if features['length'] > 30:
        raisons.append("nom très long")
    if features['is_tld_new']:
        raisons.append(f"TLD suspect (.{domain.split('.')[-1]})")
    if features['nb_digits'] > 4:
        raisons.append("beaucoup de chiffres")
    return " · ".join(raisons) if raisons else "structure suspecte"

# ── API AdGuard Home ──────────────────────────────────────────────────────────
def get_recent_queries():
    try:
        r = requests.get(f"{HG_BASE}/control/querylog",
                         auth=(HG_USER, HG_PASS),
                         params={"limit": 100}, timeout=5)
        return r.json().get("data", [])
    except Exception as e:
        print(f"{ROUGE}Erreur API AdGuard : {e}{RESET}")
        return []

def get_regles_actuelles():
    try:
        r = requests.get(f"{HG_BASE}/control/filtering/status",
                         auth=(HG_USER, HG_PASS), timeout=5)
        return r.json().get("user_rules", [])
    except Exception as e:
        print(f"{ROUGE}Erreur récupération règles : {e}{RESET}")
        return []

def domain_deja_bloque(domain, regles):
    try:
        if f"||{domain}^" in regles:
            return True
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
        return any(entry["domain"] == domain for entry in logs)
    except:
        return False

def block_domain(domain, regles):
    try:
        nouvelle_regle = f"||{domain}^"
        if nouvelle_regle in regles:
            return False
        regles.append(nouvelle_regle)
        r = requests.post(f"{HG_BASE}/control/filtering/set_rules",
                          auth=(HG_USER, HG_PASS),
                          json={"rules": regles}, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"{ROUGE}Erreur blocage {domain} : {e}{RESET}")
        return False

def log_block(domain, score):
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except:
        logs = []
    logs.append({"domain": domain, "score": round(score, 3),
                 "date": datetime.now().isoformat()})
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def compter_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return len(json.load(f))
    except:
        return 0

# ── Domaines de démo ──────────────────────────────────────────────────────────
DOMAINES_DEMO = [
    "track.advertising-metrics.xyz",
    "pixel.adserver-cdn.top",
    "analytics2847.beacon-collect.online",
    "ads.doubletrack.net",
    "telemetry.spy-metrics.info",
]

# ── Boucle principale ─────────────────────────────────────────────────────────
model = joblib.load("model.pkl")

clear()
banner()
print(f"{CYAN}Chargement du modèle Random Forest...{RESET}")
time.sleep(1)
print(f"{VERT}✓ Modèle chargé — {BOLD}200 arbres de décision{RESET}{VERT} actifs{RESET}\n")
time.sleep(1)

print(f"{CYAN}Récupération des requêtes DNS depuis AdGuard Home...{RESET}")
queries = get_recent_queries()

domaines_demo_injectes = [{"question": {"name": d}, "reason": "NotFilteredNotFound"}
                           for d in DOMAINES_DEMO]
queries = domaines_demo_injectes + queries

print(f"{VERT}✓ {len(queries)} requêtes récupérées{RESET}\n")
time.sleep(1)

regles = get_regles_actuelles()

print(f"{BOLD}{'─'*62}{RESET}")
print(f"{BOLD}  {'DOMAINE':<38} {'SCORE':<25} DÉCISION{RESET}")
print(f"{BOLD}{'─'*62}{RESET}\n")
time.sleep(0.5)

bloques  = 0
analyses = 0
vus      = set()

for q in queries:
    domain = q.get("question", {}).get("name", "").strip().rstrip(".")

    # ← Correction biais www
    if domain.startswith("www."):
        domain = domain[4:]

    if not domain or domain in vus:
        continue
    if q.get("reason", "") in ["FilteredBlackList", "FilteredBlockedService"]:
        continue
    if domain_deja_bloque(domain, regles):
        continue

    vus.add(domain)
    features  = extract_features(domain)
    X         = pd.DataFrame([features])
    score     = model.predict_proba(X)[0][1]
    analyses += 1

    if score > 0.3:
        barre = barre_score(score)
        if score > SEUIL:
            decision = f"{ROUGE}{BOLD}🚫 BLOQUÉ{RESET}"
            raison   = pourquoi_suspect(features, domain)
            print(f"  {ROUGE}{domain:<38}{RESET} {barre}  {decision}")
            print(f"  {GRIS}  └─ {raison}{RESET}")
            succes = block_domain(domain, regles)
            if succes:
                log_block(domain, score)
                bloques += 1
        else:
            decision = f"{JAUNE}⚠ SUSPECT{RESET}"
            print(f"  {JAUNE}{domain:<38}{RESET} {barre}  {decision}")
        time.sleep(0.4)

print(f"\n{BOLD}{'─'*62}{RESET}")
print(f"\n{BOLD}  RÉSUMÉ{RESET}")
print(f"  {CYAN}Domaines analysés  :{RESET} {analyses}")
print(f"  {ROUGE}Domaines bloqués   :{RESET} {BOLD}{bloques}{RESET}")
print(f"  {VIOLET}Total liste IA     :{RESET} {compter_logs()} domaines")
print(f"  {GRIS}Seuil de décision  : {SEUIL:.0%}{RESET}")
print(f"\n{VERT}{BOLD}✓ Analyse terminée — {datetime.now().strftime('%H:%M:%S')}{RESET}\n")
