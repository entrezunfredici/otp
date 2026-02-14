# Plan de recette — Release} —}

## 1) Contexte

- Produit : {{PROJECT_NAME}}
- Périmètre de la release : {{SCOPE}}
- Référence backlog : {{LINK_BACKLOG}}
- Objectifs (KPI) : {{KPI}}

## 2) Environnement & prérequis

- Pré-prod : {{URL_PREPROD}}
- Base de données / données de test : {{DATASET}}
- Comptes de test : {{ACCOUNTS}}
- Contraintes : {{CONSTRAINTS}}

## 3) Stratégie de recette

- Types : fonctionnelle / non-régression / perf légère / sécurité légère / accessibilité
- Critères de passage : {{PASS_CRITERIA}}
- Critères d’arrêt : {{STOP_CRITERIA}}

## 4) Cas de test (scénarios)

| ID     | Parcours           | Préconditions | Étapes (résumé) | Attendu | OK/KO | Observations |
| ------ | ------------------ | -------------- | ------------------ | ------- | ----- | ------------ |
| UAT-01 | Connexion          | ...            | ...                | ...     |       |              |
| UAT-02 | Leitner — session | ...            | ...                | ...     |       |              |

## 5) Non-régression (checklist rapide)

- [ ] Auth / session
- [ ] CRUD principal
- [ ] Notifications / emails
- [ ] Droits / rôles
- [ ] Mobile / responsive
- [ ] Logs / monitoring

## 6) Anomalies

| Bug     | Gravité (P1/P2/P3) | Statut | Lien     | Commentaire |
| ------- | ------------------- | ------ | -------- | ----------- |
| {{BUG}} | P1                  | Open   | {{LINK}} | ...         |

## 7) Décision Go/No-Go

- Go / No-Go : {{DECISION}}
- Conditions (si Go sous réserve) : {{CONDITIONS}}
- Date de mise en prod : {{DATE_PROD}}

## 8) Sign-off

- QA / test : {{NAME}}
- PO / métier : {{NAME}}
- Tech lead : {{NAME}}
