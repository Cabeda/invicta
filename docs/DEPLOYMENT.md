# Demo deployment

- Public demo: <https://invicta-dusky.vercel.app>
- Source repository: <https://github.com/Cabeda/invicta>
- Vercel project: `invicta`, workspace `jos-cabedas-projects`.
- Dashboard: <https://vercel.com/jos-cabedas-projects/invicta>
- Repository default branch: `main`.

Published through Vercel CLI on 28 October 2026. The stable production alias is public; Vercel's individual deployment URLs may require the account's authentication. Share the public alias above.

## Update the demo

Regenerate any changed experiment outputs locally and review the complete static export. Prepare the deployment manifest, commit and push the site and manifest, then deploy from the repository root:

```sh
node scripts/prepare-deployment.mjs
# Commit and push all changes before deployment.
vercel whoami
# If needed: vercel login
vercel link --project invicta --scope jos-cabedas-projects --yes
vercel deploy --prod --yes --scope jos-cabedas-projects --build-env INVICTA_ASSET_COMMIT="$(git rev-parse HEAD)"
```

The CLI deploys the checked-in `prototypes/costa-cabral/proposal` output. `vercel.json` skips installation and restores large public assets during the build. `.vercelignore` omits local simulation environments, source input caches and native run folders from CLI uploads. Local project IDs in `.vercel/` are ignored by Git.

The full native replay exceeds the Hobby CLI source-upload allowance. `deployment-assets.json` records every public file larger than 1 MB. The generated block in `.vercelignore` omits those bytes from the CLI upload; `scripts/stage-deployment-assets.mjs` retrieves them from `INVICTA_ASSET_COMMIT` in the public GitHub repository, verifies size and SHA-256, then puts them in the static output. Missing or mismatched files fail the build. The commit must already be pushed. No GitHub token, persistent Git integration or runtime GitHub request is needed.

The downloadable website bundle retains all files and can be served directly over HTTP(S), independently of this deployment step.

GitHub and Vercel are managed independently. Automatic GitHub deployment integration was not enabled: the automatic approval review rejected adding persistent repository access and webhooks. A new source push therefore needs a separate `vercel deploy --prod` command to publish.

## Verification

The production alias returned HTTP 200 without cookies or account authentication. The page, JavaScript modules, legacy study, report, 3D scene and both busy-case native replays matched the local export byte for byte. Browser-style compression negotiation retained valid gzip payloads for the viewer's own `DecompressionStream`. Legacy `/proposal/…` paths redirect to the corresponding published paths.

The extended701 release also verified16 Porto stops,15 interval controls, the whole-line service model's63 workings/3,024 calls, restored service settings in shared links, and the rebuilt Bolhão3D scene. Static response snapshots retain publisher bytes through `.gitattributes`, including original whitespace; their SHA-256 hashes remain verifiable.
