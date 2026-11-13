# Everyday, examined

A Quarto journal for four data projects. The site source is isolated under
`site/`; the planning and evidence artifacts at the repository root are not
part of the website.

## Build locally

Install Quarto 1.7.34 and Python 3, then run:

```sh
quarto render site
python3 site/check-output.py site/_site
quarto preview site
```

The site build disables computational execution and does not download data or
run project analyses. `site/_site/` is generated and ignored by Git.

## Publishing posts

Start with `site/drafts/weekly-post-template.qmd`. Drafts are excluded from
rendering and deployment. Use only reviewed, stable exports in `site/figures/`;
never add learner-level data, raw datasets, notebook outputs, or private
planning documents to the site tree. Before publishing, verify aggregate
disclosure controls, all claims, exact analysis revision links and actual
dates. Move a reviewed post to `site/posts/` with `draft: false`, an ISO
coverage `date`, an actual ISO `publication-date`, and a full commit-pinned
analysis code link. The pre-render check rejects draft, future-dated, unlinked,
or computationally executable posts. The archive orders published posts by
coverage date; unassigned proposed weeks do not become posts.

## GitHub Pages

The included Actions workflow renders the curated site and deploys
`site/_site/` on pushes to `main` or manual runs. In the repository's
**Settings → Pages**, choose **GitHub Actions** as the build and deployment
source; allow the workflow and `github-pages` environment to deploy if the
repository or organization requires approval. The configured canonical site
URL uses the `/blog/` project path. Nothing here changes repository settings
or asserts that a deployment has succeeded.