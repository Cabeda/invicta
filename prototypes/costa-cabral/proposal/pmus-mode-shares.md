# PMUS mode shares and traveller coverage for Costa Cabral

Checked **28 October 2026**. Purpose: provide dated reference inputs for a transparent person-trip/mode-transition calculator while retaining the distinction from a calibrated metropolitan traffic forecast.

## Sources and version verification

The [official consultation page](https://mobilidade.cm-porto.pt/destaque/pmus-discussao-publica) links the [Diagnostic Report](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf), [Measures](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Medidas.pdf), and [Action Sheets](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Fichas%20Acao.pdf). Each official download was streamed and SHA-256 compared with the local source in `/Users/jose.cabeda/Git/pmus-porto/`: **all three are byte-identical**.

| Published file | Bytes | SHA-256 |
| --- | ---: | --- |
| Diagnostico | 32,459,130 | `413e65c010a1a533a57964c8e3bcda5d50af3f13d37ad1befbbf967052372629` |
| Medidas | 15,348,788 | `f71bdcf7565e8992be276e77cd7eb42ff86a987becfaa7fd8c9627b243e95d1e` |
| Fichas Acao | 11,163,854 | `436ee3d87f286d9b4ccb668e68bad8bda5b1e9565fe1947a2b37c367db75af66` |

The diagnosis revision history includes version 4.0 dated 14 August 2026. A new publication date does not make its census, IMob or survey observations current-year data. Numeric source pages below were extracted with `pdftotext` and their relevant tables/charts visually checked from rendered PDF pages. “Printed page” means the footer label; “PDF page” is one-based file position.

## Metropolitan population and denominator

- **Census 2021:** AMP **1,736,228** residents; Porto municipality **231,800**. Confirmed in Diagnostic Table 1, printed p.8 / PDF p.19. [Source](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=19).
- Diagnostic Table 2 lists AMP **1,861,727** and Porto **273,476**, but has conflicting year labels: its title says **2025**, while the data column and variation header say **2026**, citing INE 2026. Preserve this editorial issue; use direct INE verification to label the estimates' reference year. Printed p.9 / PDF p.20. [Source](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=20).
- The PMUS Census 2021 regional comparison reports **68% car, 14% active modes, 16% public transport** for AMP, and **54% / 23% / 22%** for Porto. These are rounded **commuting** shares, not all-purpose travel shares. Figure 7, printed pp.16–17 / PDF pp.27–28. [Source](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=27).

Population is a scale/context input. A resident is not a trip, and an AMP resident's journey need not pass through Costa Cabral.

## Porto survey: exact all-purpose modal references

Figure 55, printed p.91 / PDF p.102, contains the following **person-trip** shares. Use the chart values rather than silently replacing them with rounded narrative text. These are Porto survey cohorts, not an AMP-wide representative mode split. [Diagnostic Figure 55](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=102).

| Survey cohort / day | Car | Walk | Bicycle | Bus | Metro | Train | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Porto residents, all weekday trips | 56.8% | 14.1% | 2.0% | 11.1% | 11.7% | 0.7% | 3.5% |
| Nonresidents, all weekday trips recorded | 36.5% | 4.4% | 0.7% | 25.5% | 24.2% | 6.9% | 1.9% |
| Porto residents, nonworkday | 65.5% | 12.3% | 2.1% | 5.9% | 8.3% | 1.4% | 4.6% |
| Nonresidents, nonworkday trips recorded | 54.0% | 9.2% | 2.0% | 10.4% | 16.7% | 4.5% | 3.2% |

Rows sum to 99.9–100.1% because of published rounding. Preserve the printed values in citations; disclose any normalisation used internally by a calculator. “Other” is an aggregate, including motorcycles, taxis and app-based vehicles in the report's description, rather than a licence to classify all those users identically in a restriction policy.

Important survey limits, printed pp.71–77, 89–90 / PDF pp.82–88, 100–101:

- Fieldwork dates are **15 October–9 December**; the fieldwork paragraph omits the year. **2024 is inferred** from revision 2.0 dated 23 December 2024, which incorporates survey results.
- Printed p.71 describes a target of **4,739** responses (2,373 residents, 2,366 nonresidents); p.72 reports selected analysis counts of **2,382 + 2,367 = 4,749**. Do not silently present one as an unambiguous achieved total.
- The nonresident survey is introduced as workers/students in Porto, with a substantial student component. Its shopping/leisure trips do not establish a representative census of all tourists, shoppers or visitors.
- Respondents under 16 were excluded; diaries describe the previous day, at most ten trips. Nonresident diaries deliberately omit trips with neither origin nor destination in Porto.
- Residents average **2.6 trips/day**. The report deliberately gives no corresponding nonresident rate because of that truncation. This is not a valid multiplier for all AMP residents. [Survey method](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=82), [diary structure](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=86), [trip rate](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=101).

## Purpose references include shoppers, leisure and accompanying others

Figure 53, printed p.89 / PDF p.100. **The denominator excludes return-home trips**, unlike the all-trip modal table above. [Diagnostic Figure 53](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Diagnostico.pdf#page=100).

| Cohort / day | Shopping | School | Work | Leisure | Accompany others | Personal matters | Other activity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Residents, weekday | 6.2% | 9.5% | 40.7% | 13.8% | 14.4% | 12.5% | 3.0% |
| Nonresidents, weekday | 2.1% | 31.2% | 43.4% | 8.7% | 5.6% | 6.5% | 2.5% |
| Residents, nonworkday | 12.8% | 1.8% | 27.7% | 27.9% | 13.4% | 12.4% | 4.0% |
| Nonresidents, nonworkday | 5.9% | 5.5% | 32.5% | 30.3% | 8.9% | 12.5% | 4.4% |

There are chart/narrative inconsistencies: weekday resident accompanying is **14.4% in the chart / 14.6% in text**; nonworkday resident shopping is **12.8% / 12.4%**, accompanying **13.4% / 13.7%**, personal **12.4% / 12.5%**. Figure 55 also shows **27.5% nonresident commuting bus share**, whereas its narrative says **25.5%**. The all-weekday-trip bus value is separately **25.5%**. Preserve the distinction rather than mixing those categories.

These are marginal distributions. They do **not** provide a verified mode × purpose × OD × time-of-day table. Treat an assumed combination as synthetic, and do not infer how likely a shopper is to change mode merely from the shopping share.

## Genuine AMP all-trip reference: INE IMob 2017

The original INE publication is available from the [official transport regulator](https://www.amt-autoridade.pt/media/1829/inquerito_mobilidade_funcionalidade_territorio_aml_amp_2017_ine.pdf). Its printed pp.33–35 / PDF pp.35–37 establish approximately **3.4 million person trips/day**, **1.3 million mobile people**, and **2.72 trips/day per mobile person**, for **AMP residents aged 6–84**, across the whole week. It excludes non-AMP residents and professional transport work journeys; destinations need not be inside AMP.

Figure 18, printed p.35 / PDF p.37: **car 67.6%** (driver 50.7%, passenger 16.9%), **bus 8.2%**, **metro 2.0%**, **train 0.8%**, **active 18.9%**, **motorcycle/moped 1.3%**, **other 1.2%**. Bicycle is separately **0.4%**, so walking **18.5%** is a subtraction from the active total. Bus includes employer/school services; other includes taxi, boat and air. [Mode definition and values](https://www.amt-autoridade.pt/media/1829/inquerito_mobilidade_funcionalidade_territorio_aml_amp_2017_ine.pdf#page=37).

The historical **1.56 persons/car** figure concerns **car-driver stages**, not whole principal-mode person trips or current Costa Cabral occupancy. Printed p.40 / PDF p.42. Do not combine it mechanically with principal-mode shares as an exact vehicle count. Nor should 2.72 be multiplied by the whole current population: it is a rate for mobile people in the surveyed age range. [Occupancy scope](https://www.amt-autoridade.pt/media/1829/inquerito_mobilidade_funcionalidade_territorio_aml_amp_2017_ine.pdf#page=42).

## Observed shares and 2035 targets must stay separate

The published Measures report conflicts internally:

| Porto commuting target, 2035 | Walk | Bicycle | Public transport | Car |
| --- | ---: | ---: | ---: | ---: |
| Narrative, printed p.196 / PDF p.204 | 22% | 5% | 27% | 45% |
| Table 49, printed p.197 / PDF p.205 | 23% | 5% | 34% | 37% |

Table 49's “Base (2024)” modal entries carry a footnote identifying **Census 2021**. Neither target set is an observed outcome, an AMP all-trip forecast, or a validated effect of restricting Costa Cabral. Keep this conflict visible or obtain municipal clarification before presenting a single official preset. [Narrative](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Medidas.pdf#page=204), [Table 49](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Medidas.pdf#page=205).

Action TP.02 proposes additional dedicated BUS corridors **without eliminating car circulation**. A two-direction Costa Cabral restriction is a separate experiment and must not be represented as that action's validated design. SU.07 proposes repeated mobility surveys to monitor behaviour. [TP.02, printed p.53 / PDF p.57](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Fichas%20Acao.pdf#page=57), [SU.07, printed p.13 / PDF p.17](https://mobilidade.cm-porto.pt/files/uploads/cms/PMUS%20Fichas%20Acao.pdf#page=17).

## Implications for the prototype

Recommended model distinctions, rather than observed findings:

1. Represent **residence, journey purpose and access eligibility separately**. Include nonresident shoppers, workers, students, leisure visitors, personal/health/escort trips and deliveries, including journeys that do not pass through the corridor. Permits are a policy rule; employment or shopping is a travel purpose.
2. Show **initial disruption with fixed requested journeys and mode shares**: diversions, parking/last-leg access, delays, failures and passenger impacts. Retain legitimate access scenarios rather than dropping inconvenient trips.
3. Show **conditional adaptation cases** beside that initial case: zero, low and higher mode shifts under explicit improvements to frequency, reliability, fares, walking/cycling connections and access. Shift person journeys transparently; do not equate a mode change with a cancelled trip.
4. Keep any population-scale arithmetic separate from the corridor replay. Report effects by traveller group, generalised travel time, transit capacity/crowding, retail/service access and unserved demand. Mode-shift shares alone do not prove lower total delay, improved business turnover or sufficient bus capacity.

The PMUS and IMob references improve the realism of assumptions and expose gaps. They do not supply current corridor counts, joint trip chains, local elasticities or measured causal responses to this restriction.
