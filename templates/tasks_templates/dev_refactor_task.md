# [TITRE] — dev (Scope/Module)

## Métadonnées

- ID: T-0000
- Type: dev
<!-- Choix: dev | ux-ui | devops | infra | qa | sec | doc | produit | research -->
- Statut: todo
<!-- Choix: backlog | todo | in_progress | review | blocked | done -->
- Priorité: P2
<!-- Choix: P0 | P1 | P2 | P3 -->
- MoSCoW: Must
<!-- Choix: Must | Should | Could | Won''t -->
- Estimation: M
<!-- Choix: XS | S | M | L | XL ou 2h, 1j, 3j -->
- Owner: @owner
- Deadline:
- Liens:

## Contexte

- Pourquoi on le fait ?
- Contexte métier / technique / utilisateur :

## Objectif

- Résultat attendu (une phrase claire) :

## Périmètre

**IN**
--

**OUT**
---

## Dépendances & risques
Dépendances:
  - (Bloquante) T-0123 — “…” — Owner: @… — Attendu: …
  - (Non-bloquante) T-0456 — “…” — Attendu: …
  - (Externe) Accès / validation / fournisseur — Détail: …

- Risques:
  - R1 (Prob: Low/Med/High | Impact: Low/Med/High) — Description — Signal d’alerte: … — Mitigation: …
  - R2 (Prob: … | Impact: …) — …

- Plan B:
  - Si R1 arrive → alternative: …
  - Si blocage sur dépendance → contournement: …
  - Rollback / désactivation feature flag: …

## DoD (Definition of Done)

- [ ] Fonctionnel conforme aux critères d’acceptation
- [ ] Tests OK (unit/int/e2e selon cas)
- [ ] Revue faite / validée
- [ ] Doc/Changelog mis à jour si nécessaire
- [ ] Déployé / livré (si applicable)

## Notes / Journal

- YYYY-MM-DD:

# [REFACTOR] — Sujet

## Branche Git

- Nom: dev_refactor/xxx
- Base: main | dev | release/x.y

## Problème actuel

## Branche Git

- Nom: feature/xxx | fix/xxx | refactor/xxx | chore/xxx | ci/xxx
- Base: main | develop | release/x.y
- Odeurs de code / complexité / duplications:
- Dette (impact: bugs, lenteur, maintenabilité):

## Objectif

- Ce qui doit être amélioré (mesurable):

## Stratégie

- Étapes:
- Ce qu’on ne change PAS (sécurité):

## Risques & compat

- Risques:
- Plan rollback:

## DoD spécifique

- [ ] Pas de changement fonctionnel (ou explicitement listé)
- [ ] Couverture tests maintenue/améliorée
- [ ] Perf identique ou meilleure


