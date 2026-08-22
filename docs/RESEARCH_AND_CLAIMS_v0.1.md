# BOOK OS — RESEARCH ENGINE & CLAIM LEDGER v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Goal

Make factual and evidentiary work traceable enough that BOOK OS cannot quietly invent research, statistics, authors or sources.

## 2. Research pipeline

`Research Question → Search Plan → Source Discovery → Source Normalization → Source Fetch/Inspect → Claim Extraction/Registration → Evidence Link → Evidence Analysis → Fact-check Decision`

Research is driven by Book/Chapter Contracts and unresolved claims, not by unbounded autonomous browsing.

## 3. Source adapters for v0.1

### Priority adapters

- Web search provider adapter (provider-neutral interface).
- OpenAlex — scholarly graph/discovery.
- Crossref REST — DOI/bibliographic metadata normalization.
- Semantic Scholar Academic Graph — paper/citation/author discovery and complementary metadata.
- Direct official/public web source fetch for primary/authoritative documents.
- User-imported files/notes as explicit sources.

### Later / domain-specific adapters

Government statistics, SEC/company filings, legal/regulatory databases, industry datasets, library/publisher databases, depending on book profile and licensing.

## 4. Research adapter contract

Each adapter returns normalized candidate records rather than prose conclusions:

- provider/source adapter;
- external ID(s);
- canonical title;
- authors/organization;
- publication date;
- source type;
- URL/DOI/identifier;
- abstract/summary where legally available;
- access metadata;
- raw provider metadata reference;
- fetch status;
- license/access constraints when known.

The Research Engine deduplicates DOI/URL/title variants before adding sources to the ledger.

## 5. Claim types

A Claim may be classified as:

- `QUANTITATIVE` — number/rate/amount;
- `EMPIRICAL` — observation supported by research/data;
- `CAUSAL` — X causes/contributes to Y;
- `HISTORICAL` — event/date/sequence;
- `ATTRIBUTION` — person/organization said/did something;
- `CASE_ASSERTION` — assertion about a company/person/case;
- `LEGAL_REGULATORY` — law/rule/regulatory statement;
- `CONSENSUS` — characterization of field/professional consensus;
- `INTERPRETIVE` — reasoned interpretation based on evidence;
- `AUTHORIAL` — explicitly presented as author judgment/experience rather than external fact.

Claim type influences required evidence and fact-check severity.

## 6. Evidence standard

`Source != Evidence != Claim`.

Evidence connects a specific source to a specific claim and records:

- `SUPPORTS | PARTIALLY_SUPPORTS | CONTRADICTS | CONTEXT_ONLY`;
- exact supporting location/pointer;
- strength;
- limitations;
- population/context/time constraints;
- conflicting sources;
- reviewer/fact-check decision.

A citation in the bibliography is not evidence by itself.

## 7. Source quality signals

Do not collapse source quality into a single universal “truth score”. Store signals such as:

- primary vs secondary;
- peer-reviewed vs non-peer-reviewed;
- official/statutory/company-primary source;
- sample/method availability;
- recency/freshness relevance;
- retraction/correction signal when discoverable;
- conflict of interest/sponsorship when material;
- reputation/venue metadata;
- access to full source vs metadata/abstract only.

Profile-specific policy decides what is adequate for a particular claim.

## 8. Claim verification states

`UNREVIEWED | SUPPORTED | PARTIALLY_SUPPORTED | DISPUTED | UNSUPPORTED | REJECTED`

Material claims required for Literary Master must be resolved according to the Book Contract evidence policy, or explicitly waived by human decision with reason.

## 9. Anti-hallucination gates

BOOK OS must never mark a model-generated citation as verified merely because the citation looks plausible.

For a factual source-backed claim, verification requires one of:

1. source was successfully retrieved/inspected and Evidence points to a real location; or
2. source metadata is verified but full content is unavailable, in which case the evidence is limited accordingly and cannot masquerade as full verification.

If a model proposes a DOI/URL/title that cannot be resolved, it is `UNVERIFIED_CANDIDATE`, not a Source supporting a claim.

## 10. Copyright/access discipline

- store bibliographic metadata freely where permitted;
- store only the necessary supporting excerpt/pointer and respect source terms/copyright;
- do not bulk-copy paywalled copyrighted works into BOOK OS without lawful user access/rights;
- user-provided source files retain explicit provenance;
- source access limitations are visible to fact checkers.

## 11. Research cache

Fetched metadata and legally cacheable content may be cached locally with:

- source ID;
- fetched timestamp;
- adapter/version;
- content hash;
- freshness/expiry policy;
- original URL.

Reproducibility matters: a final claim should identify the evidence snapshot used at release.

## 12. External technology baseline checked 2026-08-22

- OpenAlex help/API reference: `https://help.openalex.org/`
- Crossref REST API: `https://api.crossref.org/` and `https://www.crossref.org/documentation/retrieve-metadata/rest-api/`
- Semantic Scholar API: `https://www.semanticscholar.org/product/api`

Semantic Scholar currently exposes Academic Graph/recommendation/dataset APIs; Crossref provides open REST metadata access; OpenAlex provides a comprehensive scholarly index/API. These are discovery/metadata layers, not substitutes for source reading and claim-level evidence analysis.
