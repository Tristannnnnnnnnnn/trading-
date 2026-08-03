# Trading Signal Detector

Détecteur de signaux RSI (survente/surachat) avec dashboard web et alertes Telegram, pour une liste d'actifs eToro / cTrader.

- RSI calculé avec le lissage de Wilder (RMA), comme TradingView/eToro — pas une EMA/SMA générique.
- Source de prix actuelle : Yahoo Finance (`yfinance`). Bémol connu : prix mid-market, peut légèrement différer du bid affiché sur eToro ou du flux cTrader — à calibrer si besoin (comparer une valeur RSI affichée sur ta plateforme avec celle du dashboard).

## 1. Configurer la liste d'actifs

Éditer `config/tickers.json` :

```json
{
  "rsi_period": 14,
  "default_interval": "1d",
  "check_interval_minutes": 15,
  "thresholds": { "oversold": 30, "overbought": 70 },
  "assets": [
    { "display_name": "Apple", "yahoo_symbol": "AAPL", "platform": "eToro" },
    { "display_name": "EUR/USD", "yahoo_symbol": "EURUSD=X", "platform": "cTrader" }
  ]
}
```

Le `yahoo_symbol` doit être le ticker tel que reconnu par Yahoo Finance (ex : `EURUSD=X` pour le forex, `GC=F` pour l'or, `^GSPC` pour le S&P 500). Ce fichier est modifiable directement depuis GitHub (donc depuis ton téléphone/iPad, sans coder).

## 2. Créer le bot Telegram (pour les alertes)

1. Dans Telegram, parle à **@BotFather** → `/newbot` → suis les étapes → il te donne un `TELEGRAM_BOT_TOKEN`.
2. Envoie un message à ton nouveau bot (n'importe quoi), puis va sur `https://api.telegram.org/bot<TON_TOKEN>/getUpdates` dans un navigateur pour récupérer ton `chat.id` → c'est ton `TELEGRAM_CHAT_ID`.
3. Copie `.env.example` en `.env` et renseigne les deux valeurs.

## 3. Lancer en local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Dashboard sur http://localhost:8000

## 4. Déployer pour y accéder depuis tel/iPad/PC

Déployer sur un hébergeur type Render ou Railway (plan gratuit pour commencer) :
- Build command : `pip install -r requirements.txt`
- Start command : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Variables d'env : `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

⚠️ Sur les plans gratuits, le service peut se mettre en veille après inactivité, ce qui interrompt la surveillance en arrière-plan — si les alertes doivent être fiables 24/7, prévoir un plan payant ou un petit VPS toujours actif.

## Notes

- Les alertes ne se déclenchent qu'au **passage** d'un seuil (pas à chaque cycle tant que le RSI reste en zone survente/surachat), pour éviter le spam.
- Prochaine étape envisagée : brancher l'API cTrader Open pour des prix exacts sur les actifs du challenge funded, et enrichir avec l'historique pour l'analyse de stratégie.
