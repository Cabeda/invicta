# Demo deployment

- Public demo: <https://invicta-dusky.vercel.app>
- Source repository: <https://github.com/Cabeda/invicta>
- Vercel project: `invicta`, workspace `jos-cabedas-projects`.
- Dashboard: <https://vercel.com/jos-cabedas-projects/invicta>
- Repository default branch: `prototype/costa-cabral-access`.

Published through Vercel CLI on 28 October 2026. The stable production alias is public; Vercel's individual deployment URLs may require the account's authentication. Share the public alias above.

## Update the demo

Regenerate any changed experiment outputs locally, review the static export, commit and push source changes, then deploy from the repository root:

```sh
vercel whoami
# If needed: vercel login
vercel link --project invicta --scope jos-cabedas-projects --yes
vercel deploy --prod --yes --scope jos-cabedas-projects
```

The CLI deploys the checked-in `prototypes/costa-cabral/proposal` output. `vercel.json` skips installation and building. `.vercelignore` omits local simulation environments, source input caches and native run folders from CLI uploads. Local project IDs in `.vercel/` are ignored by Git.

GitHub and Vercel are managed independently. Automatic GitHub deployment integration was not enabled: the automatic approval review rejected adding persistent repository access and webhooks. A new source push therefore needs a separate `vercel deploy --prod` command to publish.

## Verification

The production alias returned HTTP 200 without cookies or account authentication. The page, JavaScript modules, legacy study, report, 3D scene and both busy-case native replays matched the local export byte for byte. Browser-style compression negotiation retained valid gzip payloads for the viewer's own `DecompressionStream`. Legacy `/proposal/…` paths redirect to the corresponding published paths.
