# 0004 — BSL 1.1 license, Apache 2.0 after 4 years

- **Status:** accepted
- **Date:** 2026-04-27
- **Tags:** licensing

## Context

DentalPin is open source and intends to grow a community. We also fund
development through a managed SaaS deployment and partner integrators.
A permissive license alone (Apache 2.0, MIT) lets a competing SaaS take
the codebase and operate it without contributing back, undermining the
funding model that pays for ongoing development. A pure copyleft (AGPL)
deters integrators and partner clinics from contributing.

The Business Source License 1.1 (BSL) is the middle ground used by
HashiCorp, MariaDB, CockroachDB, and Sentry: source-available, free for
non-competitive use, with an automatic conversion to a true OSS license
after a fixed number of years.

## Decision

DentalPin is licensed under **BSL 1.1**. Per-version conversion: each
released version becomes **Apache 2.0** four years after its release
date.

Use restriction (BSL "Additional Use Grant"): non-production use is
unrestricted; production use is permitted **except** for offering a
commercial managed dental clinic management service to third parties
that is substantially similar to DentalPin's own SaaS.

The Veri\*Factu module (and any other compliance module) inherits the
same license terms.

## Consequences

### Good

- Source remains fully visible, modifiable, and self-hostable by any
  clinic.
- Funding model is protected for 4 years per release, after which the
  community gets a true OSS license on that version.
- Contributors know the license trajectory upfront — no rug-pulls.

### Bad / accepted trade-offs

- Some downstream packagers (Linux distros, OSS catalogs) won't list us
  while versions are under BSL.
- Commercial competitors must negotiate a commercial license or wait
  the 4 years. We're fine with that.
- Contributor License Agreement (CLA) required so the relicense
  conversion is unambiguous.

## Alternatives considered

- **Apache 2.0 from day one.** Rejected: no protection against a SaaS
  fork undercutting the funding model that pays maintainers.
- **AGPLv3.** Rejected: deters partner integrators and self-hosting
  clinics, even though network-clause concerns are mostly theoretical.
- **Pure proprietary.** Rejected: incompatible with the project mission
  of open clinical software.

## How to verify the rule still holds

- `LICENSE` at repo root.
- Per-release `LICENSE-CONVERSION-DATES.md` (when introduced) lists the
  Apache 2.0 conversion date for each released version.

## References

- `LICENSE`
- BSL spec: <https://mariadb.com/bsl11/>
- HashiCorp BSL FAQ — used as reference for the additional-use grant
  wording
