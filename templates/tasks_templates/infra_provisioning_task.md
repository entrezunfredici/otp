# [TITRE] — infra (Scope/Module)

## Métadonnées

- ID: T-0000
- Type: infra
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

# [INFRA] — Provisioning [ressource]

## Objectif

- Ressource à créer:
- Usage (service, charge, SLA):

## Spécifications

- CPU/RAM/Storage:
- OS/Image:
- Réseau (VPC/subnet/firewall):
- Backups:
- Monitoring:

## Sécurité

- Accès (SSH keys, bastion):
- Users/permissions:
- Ports ouverts:
- Chiffrement:

## Déploiement

- IaC (Terraform/Ansible) ? lien:
- Étapes:

## Validation

- [ ] Accès OK
- [ ] Service up
- [ ] Backup/monitoring OK
- [ ] Doc d’exploitation


