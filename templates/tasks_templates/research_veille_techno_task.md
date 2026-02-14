# [RESEARCH] Veille techno — (Sujet / Domaine)

## Métadonnées

- ID: T-0000
- Type: research

<!-- Choix: dev | ux-ui | devops | infra | qa | sec | doc | produit | research -->

- Statut: todo

<!-- Choix: backlog | todo | in_progress | review | blocked | done -->

- Priorité: P2

<!-- Choix: P0 | P1 | P2 | P3 -->

- MoSCoW: Should

<!-- Choix: Must | Should | Could | Won''t -->

- Estimation: M

<!-- Choix: XS | S | M | L | XL ou 2h, 1j, 3j -->

- Owner: @owner
- Deadline:
- Liens:
  - Projet / Epic:
  - Livrables (Odoo Knowledge / dossier):
  - Problématique:
  - Besoin:
  - Benchmark archi (si existant):
  - RFC/ADR (si existant):

## Contexte

- Pourquoi cette veille maintenant ?
- Quels choix / décisions elle doit éclairer ?
- Domaine: [ex: Auth / DB / IA / Hosting / RGPD / Front / Odoo / DevOps...]

## Objectif

- À la fin, on doit avoir :
  - une synthèse courte (décision + recommandation)
  - 2–5 sources solides minimum
  - un comparatif (options + critères)
  - une décision (ou une liste de questions à trancher)

## Périmètre

**IN**

- Technologies / options à explorer: …
- Contraintes à respecter (coût, RGPD, perf, skills, délais): …
- Environnements ciblés (dev/staging/prod): …

**OUT**

- Implémentation complète (sauf PoC si nécessaire)
- Optimisations non liées au sujet

## Dépendances & risques

Dépendances:

- (Bloquante) Validation du besoin / contraintes: …
- (Non-bloquante) Accès à une doc / compte / plateforme: …
- (Externe) Avis expert / équipe / sponsor: …
- Risques:

  - R1 (Prob: Med | Impact: High) — Info biaisée / sources marketing — Signal: manque de docs officielles — Mitigation: privilégier sources primaires (docs, RFC, benchmarks neutres)
  - R2 (Prob: Med | Impact: Med) — Trop d’options → analyse infinie — Signal: >5 options — Mitigation: réduire à 2–3 “shortlist”
- Plan B:

  - Si incertitude → PoC 2h/1j max + décision “temporaire”
  - Si délai court → choisir option la plus simple/supportée + ADR

## DoD (Definition of Done)

- [ ] Questions de veille formulées (3–7 max)
- [ ] Sources listées (min 5) dont docs officielles
- [ ] Shortlist 2–3 options
- [ ] Comparatif rempli (critères + scoring)
- [ ] Recommandation + décision (ou next steps) rédigées
- [ ] Liens stockés dans Odoo Knowledge / dossier livrables
- [ ] (Optionnel) ADR créé / mis à jour

## Notes / Journal

- YYYY-MM-DD:

---

# [LIVRABLE] Veille techno — [Sujet]

## 1. Contexte & objectif

- Décision à éclairer :
- Deadline / jalon :
- Enjeux (coût / risque / qualité / délai) :

## 2. Questions de veille (3–7 max)

1) …
2) …
3) …

## 3. Contraintes & critères de choix

### Contraintes (non négociables)

- RGPD / localisation :
- Budget max :
- Tech stack imposée / préférée :
- SLA / disponibilité :
- Maintenance / compétences :
- Sécurité :

### Critères de comparaison (pondérés si besoin)

- Simplicité (mise en place / usage)
- Coût total (licence + infra + ops)
- Performance / scalabilité
- Sécurité / conformité
- Maintenabilité / communauté
- Intégration (API, Odoo, CI/CD, etc.)

## 4. Sources (minimum 5, datées)

| Source | Type (doc, blog, étude, repo) | Date | Notes |
| ------ | ------------------------------ | ---- | ----- |
|        |                                |      |       |
|        |                                |      |       |
|        |                                |      |       |

## 5. Options étudiées

### Option A — [Nom]

- Description :
- Points forts :
- Points faibles :
- Risques :
- Coût estimé :
- Pré-requis :

### Option B — [Nom]

- …

### Option C — [Nom] (si besoin)

- …

## 6. Comparatif (scoring 1–5)

| Critère          | Poids | Option A | Option B | Option C |
| ----------------- | ----: | -------: | -------: | -------: |
| Simplicité       |       |          |          |          |
| Coût total       |       |          |          |          |
| Sécurité        |       |          |          |          |
| Maintenance       |       |          |          |          |
| Perf/Scalabilité |       |          |          |          |
| Intégration      |       |          |          |          |
| **Total**   |       |          |          |          |

## 7. Recommandation

- Recommandation principale :
- Pourquoi (3–7 bullets max) :
- Conditions / garde-fous :
- Ce qu’on repousse (et pourquoi) :

## 8. Décision

- [ ] Décision prise: Oui / Non

- Si Oui: Option retenue = …
- Si Non: infos manquantes / questions restantes = …

## 9. Next steps (actions)

- Action 1 — Owner — Deadline
- Action 2 — Owner — Deadline
- (Optionnel) PoC: scope, durée max, critères de succès

## 10. Archivage

- Emplacement livrable (lien Odoo Knowledge / dossier) :
- Lien ADR (si applicable) :
