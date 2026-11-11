# TechSpecs — two-layer project architecture

## Purpose

TechSpecs has two connected but distinct parts. They share a common evidence base, but have different responsibilities.

### 1. HEATPUMPSPECS — background data and evidence infrastructure

The GitHub repository is the non-consumer-facing, evidence-led data layer.

Its purpose is to make reliable, traceable technical information about heat pumps readily available to:

- SEAI and other public authorities;
- installers and technical professionals;
- manufacturers and certification bodies;
- researchers and other interested organisations;
- AI search, retrieval and other machine-readable systems.

The repository should behave as a dependable reference resource. Its value comes from accuracy, source traceability, model-level identification, transparent uncertainty and repeatable extraction—not from sales conversion.

Operating principles:

- Follow the established TechSpecs V2 standard without redesigning it.
- Preserve original sources and provenance.
- Separate source statements, normalized facts and derived values.
- Make uncertainty, discrepancies, dates and verification status explicit.
- Never allow commercial relationships to determine technical facts, source selection, verification status or record content.
- Do not add affiliate links, lead-generation calls to action, sales rankings or promotional copy to product records.
- Keep the data layer useful and intelligible even when accessed directly, independently of the commercial website.

### 2. www.heatpumpspecs.ie — public-facing commercial service

The website is the consumer-facing and commercial layer.

Its intended purposes include:

- helping consumers understand heat-pump products and technical information;
- explaining relevant Irish grants, schemes and purchasing considerations;
- helping visitors identify appropriate suppliers or service providers;
- generating qualified enquiries and leads;
- earning affiliate revenue where suitable and transparently disclosed.

The website may present, explain and contextualize data from HEATPUMPSPECS, but it is not the canonical source of the underlying technical records.

Commercial content must be distinguishable from technical evidence. Affiliate relationships, paid placements, lead-generation arrangements and other commercial interests should be disclosed clearly. They must not change the underlying technical record or its verification status.

## Relationship between the two layers

The intended flow is:

1. Official and authoritative sources are discovered and verified.
2. Evidence is preserved and structured in HEATPUMPSPECS under the V2 method.
3. The repository exposes machine-readable records and discovery resources.
4. The website consumes or references that evidence to provide useful consumer explanations and commercial pathways.
5. Corrections to source facts are made in the canonical data layer first, then reflected on the website.

The commercial website may add editorial explanations, calculators, enquiry journeys and affiliate links. Those features do not belong in the canonical technical product records.

## Independence and trust

HEATPUMPSPECS should remain useful to SEAI and other public or technical users without requiring them to use the commercial website or participate in any commercial transaction.

The data repository is not an SEAI database, an official SEAI publication, or an SEAI-approved service. Its purpose is to make relevant evidence easier to find, inspect and reuse. Do not imply endorsement, partnership or official status unless it is explicitly established.

## Current implementation boundary

- GitHub repository: canonical working store for technical records and evidence.
- `data/catalogue.json` and `llms.txt`: interim machine-discovery resources.
- `www.heatpumpspecs.ie`: intended public-facing commercial website; not yet represented as live or integrated.
- Future publishing infrastructure may expose the repository data more conveniently, without changing the canonical V2 records.
