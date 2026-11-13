"""Verify that the Pages artifact contains only curated website outputs."""

import sys
from pathlib import Path

root = Path(sys.argv[1])
if not (root / "index.html").is_file():
    sys.exit("Missing site index; refusing to publish.")

pages = {
    "index.html", "archive.html", "methodology.html",
    "projects/groceries.html", "projects/electricity.html",
    "projects/fantasy.html", "projects/learning.html",
    "styles.css", "sitemap.xml", "robots.txt", ".nojekyll",
    "listings.json", "search.json",
}
asset_types = {".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".gif",
               ".webp", ".woff", ".woff2", ".ttf", ".eot", ".map", ".ico"}
figure_types = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
unexpected = []
for path in root.rglob("*"):
    if path.is_symlink():
        unexpected.append(str(path.relative_to(root)))
        continue
    if not path.is_file():
        continue
    rel = path.relative_to(root)
    name = rel.as_posix()
    valid = (
        name in pages
        or (rel.parts[0] == "site_libs" and path.suffix.lower() in asset_types)
        or (len(rel.parts) == 2 and rel.parts[0] == "posts" and path.suffix == ".html")
        or (len(rel.parts) >= 2 and rel.parts[0] == "figures" and path.suffix.lower() in figure_types)
    )
    if not valid:
        unexpected.append(name)
if unexpected:
    sys.exit("Refusing to publish unexpected output files:\n" + "\n".join(sorted(unexpected)))
print("Deployment artifact contains only allowed site outputs.")
