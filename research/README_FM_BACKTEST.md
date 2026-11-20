# UK FM Contract Intelligence — Retrospective Audit (5–18 November 2026)

## Outcome: NO-GO for a £399/month recruiter subscription on current evidence

A reproducible retrospective archive scan and structured enrichment were completed. **5,732 official notice/CSV records** were screened (4,564 Find a Tender XML files and 1,168 Contracts Finder OCDS CSV rows). Preliminary keyword matches: 112 FTS awards and 22 CF awards. All 112 FTS matches were extracted with no parse errors. **23 higher-priority records were manually adjudicated**, resulting in **5 signed operational contracts, 4 named awarded operational contracts, 2 broader technical contracts, 5 unsigned/pending awards, and 7 one-off, framework, or out-of-scope events**. These are commercial *contract events*, not confirmed hiring leads.

**Contract-specific vacancies causally established: 0. Paying buyer pilots: 0.** In two cases sector/geography-relevant job advertisements were found, but neither was tied directly to the named award. The original target of 12 independently useful, staffing-related opportunities is not demonstrated. Do not charge customers or promise hiring leads based on this data alone.

Government archives have a no-file weekend gap for Contracts Finder on 7, 14 and 15 November. All 14 daily Find a Tender archives were processed. November publication dates can be weeks after the actual contract signature; do not mislabel each publication as a fresh win. We made no production deployment, no customer charges, and no outbound marketing communications.

## Results and source files

- [Archive daily coverage and counts](fm-archive-results/summary.json)
- [All screened Find a Tender candidates](fm-archive-results/fts_enriched.csv)
- [Contracts Finder candidates](fm-archive-results/cf_automatically_screened.csv)
- [Human-adjudicated evidence ledger (23 records)](fm-archive-results/manual_adjudication.csv)
- [Find a Tender source census](fm-archive-results/fts_potential_awards.csv)
- [Contracts Finder source census](fm-archive-results/cf_potential_awards.csv)
- [Daily source coverage table](fm-archive-results/daily_coverage.csv)

## Important examples

- House of Commons / OCS Technical Services £325m signed hard FM contract: https://www.find-tender.service.gov.uk/Notice/107237-2026
- Kent Police / Gilbert & Stamper £1.3m electrical/UPS services: https://www.find-tender.service.gov.uk/Notice/108806-2026
- Belfast / Graham Asset Management £388,835 legionella-monitoring services: https://www.find-tender.service.gov.uk/Notice/109336-2026
- Enfield / Apex £1.8m lift maintenance award: https://www.contractsfinder.service.gov.uk/Notice/ccc033cf-4d48-479b-b8c6-34db12e2d7e1
- UEA / Robertson £35.06m FM award *pending signature* at notice date: https://www.find-tender.service.gov.uk/Notice/106241-2026

## Business decision

The data-access and automated award-identity extraction hypotheses passed. The **hire-trigger and paid-demand hypotheses did not**. No claim of 14 consecutive live-production days is made; this was a historical audit executed in sessions.

The corrective test, if pursuing the model further: **lead with first-party, currently advertised technical vacancies**, enrich them with relevant contract awards, and seek an actual paid £99 pilot before building further infrastructure. Otherwise switch to a supplier-paid recurring referral model with no product fulfilment. Data processing without sales proof is not revenue.

## Source and code

Official archives: [Find a Tender November 2026](https://www.data.gov.uk/dataset/8570ac2d-9bb5-415c-83e8-d860b6e67c4d/uk-public-procurement-notices-november-2026), [Contracts Finder November 2026](https://www.data.gov.uk/dataset/d5038a31-8666-4d6f-8d4d-7de87ed650e7/contracts-finder-notices-11-2026).

Collector: [fm-archive-scan.py](fm-archive-scan.py). Structured award enrichment: [fm-enrich.py](fm-enrich.py). All code and evidence are isolated on this research branch; `main` unchanged. The workflow is triggered only by research-branch workflow edits; no recurring production schedule was created.
