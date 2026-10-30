# STCP punctuality: contract measure and the project's stricter goal

Checked 30 October 2026, using public operator, municipal and regulator sources. **Exact-second compliance at all 714 checkpoints is Invicta's engineering acceptance rule; it is not the contractual punctuality definition established below.** This research does not change that goal or establish a compliant proposal.

## Confirmed contractual measures

Valongo publishes the signed road-service contract dated **26 December 2024**. Its Anexo 9, Chapter I, defines ordinary-bus indicators:

| Measure | Definition relevant to the simulation |
|---|---|
| CPV: departure compliance | Departures from schedule through **600 seconds late**, with no early departure. |
| CPV denominator | Completed commercial trips that start and finish at their programmed locations. |
| CPUV: first/last trip | Initial stop: **[0, +600] seconds** for both first and last trips; the last trip's final stop: **[−300, +900] seconds**. |

These are indicator definitions, not a ten-minute allowance at every intermediate stop. Clause 13 also requires feasible schedules, recovery time and proactive operation; recurrent congestion must be included in planning and does not justify lateness. [Signed contract: cover](https://www.cm-valongo.pt/cmvalongo/uploads/document/file/10130/contrato_de_servico_publico___stcp.pdf#page=1), [Clause 13, pp.29–30](https://www.cm-valongo.pt/cmvalongo/uploads/document/file/10130/contrato_de_servico_publico___stcp.pdf#page=29), [Anexo 9, pp.314–316; printed pp.4–6](https://www.cm-valongo.pt/cmvalongo/uploads/document/file/10130/contrato_de_servico_publico___stcp.pdf#page=314).

Short wording checked visually on PDF page 316: “sem a possibilidade de qualquer adiantamento”. The table and completed-trip denominator were also visually verified. Signature marks are present on pp.83–85; STCP signatures were visually checked on p.85. The downloaded 370-page public PDF has SHA-256 `80db4498936fb716030cae9bf88ddd7d1465c0b99e5094e7340e67cd539f7f78`. PDF metadata modification date is 7 March 2025; that is not the contract date.

AMT's **Parecer 55/2024**, §§57–58, pp.23–24, independently describes the ordinary-bus CPV departure window. It concerns review of draft contracts, so the signed municipal copy is the stronger source for this finding. [AMT opinion](https://www.amt-autoridade.pt/media/5277/parecer-55_dr_26set.pdf#page=23).

STCP states that its COSP has been in force since **1 January 2025**. This bounded research has not certified the absence of later amendments to the published contract. [STCP, 9 October 2026](https://stcp.pt/pt/noticias/stcp-lanca-inquerito-de-satisfacao-para-melhorar-qualidade-do-servico).

## What the older municipal result means

The municipal 2024 monitoring report, §2.2.2, printed p.15 (PDF page 15), uses contractual intervals without listing their values. Its 92.3% result pools 6,835 first/last-trip terminal inspections across twelve lines, including 701. It is neither a 701-specific result nor an all-day intermediate-checkpoint measure. Its previous contract ended in 2024; do not substitute its sampling method for the current Annex 9 definitions. [2024 monitoring report](https://mobilidade.cm-porto.pt/files/uploads/cms/Relat%C3%B3rio%20STCP%202024.pdf#page=15).

## Timetable precision

The frozen 28 October inbound route schedule contains 708 non-null arrival/departure strings at the selected timetable anchors; all have seconds `00`. This was checked in `prototypes/line-701/data/official-extension/schedule.json`, whose source is the [official STCP schedule API](https://stcp.pt/api/route/701/schedule?service_id=UTIL+ESCOLAR%3AFLUXO+3+20261027&direction_id=1). Its first Codiceira/Ermesinde references are `05:25:00` and `05:33:00`.

That data representation does **not** establish an operational zero-second tolerance, permission to round a late departure down, or a within-published-minute rule. No verified source in this check defines the 701's designated intermediate departures or all terminal arrivals as exact-second contractual obligations. The operator timetable remains the planned reference; the tolerance and event being measured must be stated separately.

## Project implications

Keep three explicit views:

1. **Strict engineering goal:** retain all 127 scheduled trips, exact origin/designated departures and no-later-than terminal arrivals. Missing trips continue to fail. Label this as the project's target.
2. **Contract indicator comparison:** calculate CPV only with its stated departure window and completed-trip denominator, alongside CV/completion and CPUV. Always display how many of the 127 trips were missing; a completed-only percentage can conceal service loss. Do not apply 600 seconds to all 714 checkpoints or describe this calculation as a legal compliance determination.
3. **Passenger experience:** show seconds/minutes early or late, headway gaps, waiting and crowding, including people whose requested journey does not finish.

A 5- or 19-second Ermesinde diagnostic miss therefore fails the strict project test, but this source does not establish it as a breach of CPV: CPV concerns trip departures, not that intermediate checkpoint. The discovered window is a reporting distinction, not a reason to relax the goal, tune driver physics or relabel diagnostic probes as successful passenger service.
