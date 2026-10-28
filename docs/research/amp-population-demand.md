# Metropolitan population and a defensible demand basis

Checked 28 October 2026. Primary-source research for the Costa Cabral prototype; this note does not create a calibrated metropolitan traffic model.

## Confirmed population figures

The official INE JSON service was read successfully for both indicators below. The annual population estimate and the census count are different statistical products and dates.

| Geography | Annual resident-population estimate, 31 December 2025 | Census 2021 resident population |
|---|---:|---:|
| Área Metropolitana do Porto (AMP) | **1,861,727** | **1,736,228** |
| Porto municipality | **273,476** | **231,800** |

The annual series is INE indicator **0012918**, “População residente … Local de residência (NUTS - 2024), Sexo e Grupo etário”; the returned latest reference year is `2025`, with `DataUltimoAtualizacao` **2026-06-22**. Extracted total-sex (`dim_3=T`) and total-age (`dim_4=T`) records: AMP `geocod=11A`, Porto municipality `geocod=11A1312`. [Official JSON](https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=0012918&lang=PT), [official catalogue and indicator description](https://dados.gov.pt/pt/datasets/populacao-residente-n-o-64).

The census series is INE indicator **0014584**, “População residente … à data dos Censos [2021] (NUTS - 2024 - geografia 2025) e Sexo”; the response says reference `2021`, updated **2025-10-28**. Extracted total-sex records use AMP `11A` and Porto municipality `1312`. Do not join territorial identifiers across these two responses without an explicit crosswalk. [Official census JSON](https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=0014584&lang=PT), [catalogue](https://dados.gov.pt/pt/datasets/populacao-residente-n-o-104/).

The 2025 annual estimates use a new fully administrative methodology, accompanied by revision of the 2021–2024 annual series. Thus older annual values in earlier publications should not be silently combined with the new series. A census result is not replaced by calling the 2021 annual estimate “Census 2021”. INE explains this change in its July 2026 publication, pp. 8–10. [INE methodology explanation](https://www.ine.pt/ine_novidades/semin/INEWS66/index.html).

### Geographic check: 17 municipalities

The 17 municipal annual-total records below sum exactly to the AMP total, **1,861,727**. This is a check on the extracted source data, not a sum of district populations. The [AMP institution](https://www.amp.pt/) also identifies its 17 municipalities as its working territory. All numbers in this table are from the same 2025 INE response above.

| Municipality | Residents, 2025 |
|---|---:|
| Arouca | 21,459 |
| Espinho | 32,455 |
| Gondomar | 170,597 |
| Maia | 142,129 |
| Matosinhos | 181,930 |
| Oliveira de Azeméis | 70,027 |
| Paredes | 88,858 |
| Porto | 273,476 |
| Póvoa de Varzim | 72,364 |
| Santa Maria da Feira | 142,676 |
| Santo Tirso | 69,810 |
| São João da Madeira | 23,991 |
| Trofa | 41,512 |
| Vale de Cambra | 22,066 |
| Valongo | 98,930 |
| Vila do Conde | 86,245 |
| Vila Nova de Gaia | 323,202 |

## Mobility evidence has another denominator and year

AMP's first-party summary of the **IMob 2017** results reports the following metropolitan context. These are historical **person-trip main-mode shares**, not percentages of vehicles in today's traffic and not Costa Cabral counts:

| IMob 2017 measure | AMP result |
|---|---:|
| Car main-mode share | 67.6% |
| Public and/or collective main-mode share | 11.1% |
| Walking plus cycling | 18.9% |
| Cycling, included in the preceding row | 0.4% |
| Average car occupancy | 1.56 people/vehicle |
| Daily person-trips | About 3.4 million |
| Trips/day per **mobile** person | 2.72 |
| Work trip purpose | 30.3% |
| Shopping trip purpose | 18.5% |

The four mode rows overlap: cycling is included in the soft-mode total. Public/collective transport includes more than buses. The summary's geography/71% wording is not used here to derive an OD matrix. [AMP results summary, published 29 November 2018](https://www.amp.pt/en/noticia/apresentacao-dos-resultados-definitivos-do-inquerito-a-mobilidade-nas-areas-metropolitanas-do-porto-e-de-lisboa/).

The INE survey publication defines the studied age interval as **6–84 years** and reports a mobile-population rate of **78.9%** for the AMP across the overall survey period, with separate weekday/non-weekday results. Consequently multiplying the entire 2025 population by 2.72 does not reproduce the survey's population basis. [INE survey publication hosted by AMT, executive summary](https://www.amt-autoridade.pt/media/1829/inquerito_mobilidade_funcionalidade_territorio_aml_amp_2017_ine.pdf).

The companion [PMUS modal-share research](pmus-mode-shares.md) checks the municipality-specific diagnostic and policy-target figures. A Porto-municipality split must not be labelled the metropolitan split.

## Public data routes and what remains missing

- **Population:** the two JSON URLs above returned HTTP 200 and usable records. The full annual response was about 4.35 MB. Select geography/sex/age on the client, retain extraction time, update date and a content hash, and assert the expected reference year. Do not assume an untested server-side filter silently worked. The raw source snapshots and a compact 17-municipality extraction were saved under `/tmp/invicta-pop-0012918.json`, `/tmp/invicta-census-0014584.json` and `/tmp/invicta-amp-population-facts.json` for the implementation handoff.
- **Work/study travel:** the official catalogue lists INE indicator **0012369**, resident employed people/students by residence, sex, employment/student status and work/study location. It is a useful commuting-data lead. This research verified its catalogue definition, not a complete named-municipality OD matrix or street-level routes. [Official catalogue entry](https://dados.gov.pt/pt/datasets/687094558c1cd0da86633583), [INE indicator](https://www.ine.pt/xurl/indx/0012369/PT).
- **All travel purposes:** commuting data alone omits shopping, leisure/walking, care, escorting and other journeys. IMob supplies historical evidence for several of these purposes. Current local trip distributions, detailed OD, time-of-day patterns, mode availability, bus boarding/load data, route choices and corridor capture rates still require matching observations and access to suitable data.
- **Non-residents:** AMP residents visiting Porto are already part of a metropolitan resident-population basis, but people entering from outside the AMP, visitors/tourists and relevant service/freight activity require distinct external-demand inputs. Neither the resident population nor its modal split counts everyone present on Costa Cabral.

## Recommended synthetic-demand construction

This is modelling advice, not a statistical estimate derived from population alone.

1. Build a weighted representative population, stratified by municipality/zone and relevant age, car availability and accessibility needs. Full one-agent-per-resident simulation is unnecessary for a transparent first model; state each sample agent's expansion weight.
2. Generate daily activity/trip chains by residence and purpose. Distinguish corridor residents, other Porto residents, other AMP residents and external visitors; separately distinguish work, shopping, education, care/visits, leisure and other purposes. Residency and trip purpose are different dimensions.
3. Assign origins/destinations, departure intervals and available modes. Constrain totals with observed flows and bus use. Only journeys that use or are affected by the study network enter the corridor simulation; do not send 1.86 million residents down Costa Cabral.
4. Convert car **person-trips** to vehicle movements using explicit occupancy and shared-trip assumptions. Generate bus services from frequency/timetables and passengers from demand; a bus is not one person, and 11.1% public-transport trips does not mean 11.1% of vehicles are buses.
5. Hold the same people, destinations and journey purposes through an immediate-change comparison. Then test explicit mode-shift assumptions and feasible service changes. Higher bus demand must be checked against boarding time, frequency, capacity, waiting and denied boarding, rather than simply deleting car trips.
6. Report complete door-to-door person-time: walking/access, waiting, transfers, riding, parking/search and final walking where represented. Show each group's gain/loss, completion/unmet demand and upper-tail times alongside the overall mean.
7. Present short-term and long-term outputs as conditional scenarios. An average improvement can coexist with losses for some travellers. Use a break-even shift curve and report whether remaining drivers, residents, shoppers and other groups individually improve; do not label an average gain “better for everyone”.

Population can provide an auditable scale and geographic distribution. It does **not** by itself establish trips per person, corridor demand, household vehicle types, current modal split, switching speed or the causal effect of a new bus-access policy.
