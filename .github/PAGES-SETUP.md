# Enabling GitHub Pages (once per repo)

The workflow cannot turn Pages on for you: the default `GITHUB_TOKEN` is not allowed to
create a Pages site, so `enablement: true` fails with *Resource not accessible by
integration*. Do it once, either way:

**In the browser:** Settings, Pages, Build and deployment, Source, choose **GitHub Actions**.

**From the terminal:**

```bash
gh api -X POST repos/johnfisher-ai/fisher-nsduh-analysis/pages -f build_type=workflow
```

Then push, or `gh workflow run pages.yml --ref main`.

## What gets published

`public/` and nothing else. Confirm after the first deploy:

```bash
U=https://johnfisher-ai.github.io/fisher-nsduh-analysis
curl -s -o /dev/null -w "%{http_code}\n" $U/                 # expect 200
curl -s -o /dev/null -w "%{http_code}\n" $U/CLAUDE.md        # expect 404
```

A 200 on the second one means the workflow is publishing the repo root. Fix that before
you put anything private in the repo.
