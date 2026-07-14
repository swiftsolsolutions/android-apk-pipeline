# Full-cycle automation mechanics (GitHub REST API)

All calls use `Authorization: Bearer <TOKEN>`, `Accept: application/vnd.github+json`,
`X-GitHub-Api-Version: 2022-11-28`. Base: `https://api.github.com/repos/{owner}/{repo}`.

## 0. Verify access first
`GET /repos/{owner}/{repo}` → 200 means the token is scoped to this repo.
A **404** means the repo is not in the token's selected repositories (most common
setup mistake) OR doesn't exist — ask the user to attach the repo to the token.
A **403** on repo creation means the token lacks Administration (repo-creation is
account-level and can't be scoped to one repo — have the user create the empty
repo themselves, which also keeps the token narrow).

## 1. Push all files in one commit (Git Data API)
1. `GET /git/ref/heads/{branch}` → base commit sha (`object.sha`).
   `GET /git/commits/{sha}` → base tree sha (`tree.sha`). (If the branch is
   missing, the repo is empty — omit parents/base_tree.)
2. For each file: `POST /git/blobs` `{content: base64, encoding:"base64"}` → blob sha.
3. `POST /git/trees` `{base_tree: <baseTreeSha>, tree:[{path,mode:"100644",type:"blob",sha}]}`
   — including `base_tree` preserves the README and any other apps in the repo.
4. `POST /git/commits` `{message, tree:<newTreeSha>, parents:[<baseCommitSha>]}`.
5. `PATCH /git/refs/heads/{branch}` `{sha:<newCommitSha>}`.

## 2. Wait for the build
Pushing to `main` triggers the workflow. Poll:
`GET /actions/runs?per_page=1` → newest run id, then
`GET /actions/runs/{id}` until `status == "completed"`; read `conclusion`
(`success`/`failure`). For per-step detail: `GET /actions/runs/{id}/jobs`.
First builds take ~5-10 min (SDK + deps download); poll every ~15s.

## 3. Return the APK link
The workflow publishes a **prerelease**, so `GET /releases/latest` returns 404 by
design. Use `GET /releases?per_page=5`, take the newest, and read
`assets[].browser_download_url`. Give that link to the user. **Private repos**:
the link only serves the file to a signed-in GitHub session — tell the user to
open it while logged in (or, if they make the repo public, it becomes a no-login
direct download).

## 4. On failure
Read the failing step from `/actions/runs/{id}/jobs`; if logs are needed,
`GET /actions/jobs/{job_id}/logs` (redirects to a log zip). Fix the source and
repeat the push. Iterate to green rather than returning a raw error.

## Notes
- **versionCode**: don't hand-bump for Play publishes — CI assigns it via
  `VERSION_CODE=$(date +%s)` (see `assets/play-publish.yml`) and `build.gradle.kts`
  reads `System.getenv("VERSION_CODE") ?: <N>`. This guarantees every release is a
  strictly-higher, valid upgrade. If a rollout shows *"This release does not add or
  remove any app bundles"* **and** *"doesn't allow any existing users to upgrade"*,
  the versionCode wasn't higher than the live one — publish again (CI bumps it) or
  discard the stale Console draft; don't re-point a release at an existing version.
- For APK (GitHub Release) builds, a higher versionCode still matters so installs
  upgrade in place rather than erroring on downgrade.
- One commit per improvement keeps history clean and each build maps to one change.
- Keep the token only in session memory; never write it to any file, skill, or repo.
