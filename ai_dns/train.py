# train.py v2
import pandas as pd, math, joblib
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import time

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
        'length':           len(domain),
        'nb_subdomains':    len(parts) - 2,
        'nb_digits':        sum(ch.isdigit() for ch in domain),
        'nb_hyphens':       domain.count('-'),
        'has_ad_keyword':   int(any(k in domain for k in
                             ['ad','ads','track','click','pixel',
                              'analytics','telemetry','beacon','stat',
                              'metrics','collect','spy','log','cdn'])),
        'entropy':          entropy(sld),
        'digit_ratio':      sum(ch.isdigit() for ch in sld) / max(len(sld), 1),
        'sld_length':       len(sld),
        'vowel_ratio':      vowels / max(len(sld), 1),
        'consonant_ratio':  consonants / max(len(sld), 1),
        'nb_dots':          domain.count('.'),
        'tld_is_com':       int(tld == 'com'),
        'has_numbers':      int(any(ch.isdigit() for ch in sld)),
        'alpha_ratio':      alpha_ratio,
        'has_repeated':     has_repeated,
        'longest_num_seq':  longest_num,
        'tld_length':       len(tld),
        'is_tld_new':       int(tld in ['xyz','top','club','online',
                                        'site','web','info','biz']),
    }

print("Chargement des données...")
ad    = pd.read_csv("ad_domains.txt", header=None, names=["domain"])
ad["label"] = 1
legit = pd.read_csv("legit_domains.txt", header=None, names=["domain"])
legit["label"] = 0

df = pd.concat([ad.sample(15000, random_state=42),
                legit.sample(10000, random_state=42)]).sample(frac=1, random_state=42)

print("Extraction des features...")
X = pd.DataFrame(df["domain"].apply(extract_features).tolist())
y = df["label"]

print("Entraînement du modèle...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    class_weight='balanced',
    n_jobs=-1,
    random_state=42
)
model.fit(X_train, y_train)

print("\n── Résultats ──────────────────────────")
print(classification_report(y_test, model.predict(X_test)))
print("── Importance des features ────────────")
for feat, score in sorted(zip(X.columns, model.feature_importances_),
                          key=lambda x: -x[1]):
    bar = "█" * int(score * 40)
    print(f"  {feat:20s} {score:.3f}  {bar}")

joblib.dump(model, "model.pkl")
print("\n✓ model.pkl sauvegardé !")