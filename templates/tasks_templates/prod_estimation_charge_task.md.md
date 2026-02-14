# [PRODUIT] Estimation de la charge — (MVP / Version / Scope)

## Métadonnées

- ID: T-0000
- Type: produit

<!-- Choix: dev | ux-ui | devops | infra | qa | sec | doc | produit | research -->

- Statut: todo

<!-- Choix: backlog | todo | in_progress | review | blocked | done -->

- Priorité: P1

<!-- Choix: P0 | P1 | P2 | P3 -->

- MoSCoW: Must

<!-- Choix: Must | Should | Could | Won''t -->

- Estimation: M

<!-- Choix: XS | S | M | L | XL ou 2h, 1j, 3j -->

- Owner: @owner
- Deadline:
- Liens:
  - MVP & versions:
  - MoSCoW:
  - User stories:
  - Backlog Odoo (projet):
  - Schémas / archi (si existant):
  - Tableur chiffrage (si existant):

## Contexte

- On doit estimer la charge pour :
  - valider la faisabilité planning
  - décider du périmètre MVP
  - organiser les sprints (Scrumban)
- Le résultat doit être “exploitable” (pas un roman).

## Objectif

- Sortir une estimation :
  - par lots / features / epics
  - avec hypothèses explicites
  - avec capacité de l’équipe
  - + marge / risques
  - + conclusion (MVP OK / ajuster / repousser)

## Périmètre

**IN**

- MVP / version ciblée: …
- Dev + QA + DevOps + UX/UI (selon projet)
- Intégrations / migrations si concerné

**OUT**

- Optimisations/perf non demandées
- “Nice to have” non MVP (sauf si chiffré à part)

## Dépendances & risques

Dépendances:

- (Bloquante) User stories finalisées / scope MVP: …
- (Non-bloquante) Architecture validée / contraintes: …
- (Externe) Infos métiers / validation sponsor: …
- Risques:

  - R1 (Prob: Med | Impact: High) — Scope flou → estimation fausse — Signal: US sans AC / DoD — Mitigation: chiffrer seulement ce qui est “DoD-ready”
  - R2 (Prob: Med | Impact: Med) — Capacité surestimée — Signal: disponibilité non réaliste — Mitigation: capacité = temps réel dispo (réunions/interruptions)
  - R3 (Prob: Med | Impact: High) — Dépendances externes (API, accès) — Mitigation: buffer + plan B
- Plan B:

  - Si estimation trop haute → réduire MVP (Must only) + décaler Should
  - Si incertitudes → 1 sprint “spike/PoC” timeboxé

## DoD (Definition of Done)

- [ ] Périmètre MVP/version figé (même temporairement)
- [ ] WBS / lots découpés (Epics → tâches)
- [ ] Estimation faite avec méthode définie (3 points ou t-shirt/stories)
- [ ] Capacité équipe calculée (réelle)
- [ ] Marge/buffer + risques inclus
- [ ] Planning macro (sprints/jalons) proposé
- [ ] Conclusion + recommandations (ajuster scope / délais / ressources)
- [ ] Stocké dans Odoo Knowledge / livrables + liens ajoutés

## Notes / Journal

- YYYY-MM-DD:

---

# [LIVRABLE] Estimation de la charge — [MVP / Version]

## 1. Hypothèses (obligatoire)

- Périmètre estimé : [MVP / V1 / Feature set…]
- Période cible : [dates / jalon]
- Méthode d’estimation :
  - [ ] T-shirt size (XS/S/M/L/XL)
  - [ ] Story points
  - [ ] Heures/Jours
  - [ ] 3-point (Optimiste / Réaliste / Pessimiste)
- Règles :
  - Inclure QA ? Oui/Non
  - Inclure DevOps/infra ? Oui/Non
  - Inclure docs ? Oui/Non
  - Inclure marge ? Oui/Non (%)

## 2. Capacité (réelle) de l’équipe

> Capacité = dispo réelle (hors réunions, interruptions, admin, cours…)

| Rôle           | Personne | Dispo hebdo (h) | % focus | Capacité utile (h) |
| --------------- | -------- | --------------: | ------: | ------------------: |
| Dev             |          |                 |         |                     |
| QA              |          |                 |         |                     |
| UX/UI           |          |                 |         |                     |
| DevOps          |          |                 |         |                     |
| **Total** |          |                 |         |                     |

## 3. Lots / WBS (Work Breakdown Structure)

> Epic → sous-lots → tâches (niveau suffisant pour estimer)

| Epic/Lot | Description | Dépendances | Risques | Inclus MVP ? |
| -------- | ----------- | ------------ | ------- | ------------ |
| E1       |             |              |         | Oui/Non      |
| E2       |             |              |         |              |
| E3       |             |              |         |              |

## 4. Estimation par lot (brut)

### Option A: 3-point (recommandé)

| Lot | Optimiste | Réaliste | Pessimiste | Estim PERT (optionnel) |
| --- | --------: | --------: | ---------: | ---------------------: |
| E1  |           |           |            |                        |
| E2  |           |           |            |                        |
| E3  |           |           |            |                        |

> Formule PERT (si utilisée) : (O + 4R + P) / 6

### Option B: T-shirt / Story points

| Lot | Taille / SP | Justification | Niveau confiance (Low/Med/High) |
| --- | ----------- | ------------- | ------------------------------- |
| E1  |             |               |                                 |
| E2  |             |               |                                 |
| E3  |             |               |                                 |

## 5. Charges transverses (souvent oubliées)

- Tests (QA / e2e) :
- Revue / intégration :
- DevOps / déploiement :
- Documentation :
- Buffers (réunions, interruptions, imprévus) :

## 6. Buffer & risques (marge)

- Marge appliquée : __% (recommandation: 15–30% selon incertitude)
- Risques majeurs + impact sur planning :
  - R1: …
  - R2: …

## 7. Synthèse effort total

- Effort brut total (sans marge) :
- Effort avec marge :
- Capacité utile hebdo :
- Durée estimée (semaines) :
- Date cible réaliste :

## 8. Proposition de planning macro (Sprints / jalons)

| Sprint/Jalon | Objectif | Lots inclus | Critère de sortie (DoD) |
| ------------ | -------- | ----------- | ------------------------ |
| S1           |          |             |                          |
| S2           |          |             |                          |
| S3           |          |             |                          |

## 9. Conclusion & recommandations

- MVP tenable ? Oui/Non
- Si Non : quoi réduire (Must only) ?
- Décisions à prendre :
- Next steps :
  - Découper en tâches Odoo (si pas déjà fait)
  - Lancer un sprint “spike” si incertitudes
  - Valider capacité/ressources
