# Client Portal fixtures

Charger les données de test (réelles):

```bash
python manage.py loaddata client_portal.json
```

Identifiants de test:
- usera@example.com / client123
- userb@example.com / client123

URLs de test:
- /client/dashboard/
- /client/containers/
- /client/containers/201/

---

PREVIEW ONLY – DO NOT USE IN PROD

Fichier: fixtures/preview_only.json

Usage:
- Données de démo pour UI client
- Aucun User, aucun password, aucune auth
- Ne doit jamais être utilisé en prod

Charger les données preview:

```bash
python manage.py loaddata preview_only.json
```

Nettoyer les données preview:

```bash
python manage.py clear_preview_data
python manage.py clear_preview_data --older-than-days 7
```

⚠️ NE JAMAIS UTILISER EN PROD

Les routes /preview/* fonctionnent même sans charger ces fixtures (fallback mock).

Commande interactive (DEV):
- La commande demande de taper YES avant suppression.
- Ne s'exécute pas si DEBUG=False ou DJANGO_ENV=prod/production.

Exemple cron (DEV uniquement):
```bash
0 3 * * * /path/venv/bin/python /path/project/manage.py clear_preview_data --older-than-days 7
```

---

Export anonymisé depuis la base (PREVIEW ONLY – TO DELETE):

```bash
# Export par défaut (documents exclus)
python manage.py client_portal_export_fixtures --out fixtures/client_portal_export.json --limit 200

# Export avec documents
python manage.py client_portal_export_fixtures --include-docs --out fixtures/client_portal_export.json

# Export par client
python manage.py client_portal_export_fixtures --client-id 1 --out fixtures/client_portal_export.json

# Exclure des champs supplémentaires
python manage.py client_portal_export_fixtures --extra-exclude "User:full_name" --extra-exclude "Client:address" --out fixtures/client_portal_export.json

# Export uniquement certains modèles
python manage.py client_portal_export_fixtures --only-models "Client,Container,TrackingEvent" --out fixtures/client_portal_export.json
```

Options:
- --include-docs / --exclude-docs (mutuellement exclusives, défaut = exclude)
- --only-models "Client,Container,TrackingEvent,Document"
- --extra-exclude "Model:field1,field2" (répétable)
- --no-mask (DEV ONLY, affiche un warning)
- --strict (refuse l’export en environnement PROD-like)
- --i-know-what-i-am-doing (override strict, DEV ONLY)

Strict mode (exemples):
```bash
python manage.py client_portal_export_fixtures --strict --out fixtures/client_portal_export.json
python manage.py client_portal_export_fixtures --strict --i-know-what-i-am-doing --out fixtures/client_portal_export.json
```

Avertissement: NE PAS exporter en prod. Le script anonymise les emails/téléphones et exclut les mots de passe.

Mini test manuel:
1) python manage.py client_portal_export_fixtures --out fixtures/client_portal_export.json
2) python manage.py loaddata fixtures/client_portal_export.json
3) Vérifier /client/dashboard/
