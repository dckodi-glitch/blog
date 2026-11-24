"""Verify that the Pages artifact contains only curated website outputs."""

import hashlib
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
grocery_assets = {
    "posts/grocery-2023-06-14-assets/price-history.svg": "e97b9709e1f74b84e2c6a9561593f726ef742085d744d2374009dd9f9a5b9863",
    "posts/grocery-2023-06-14-assets/monthly-prices.csv": "9f5485711a21f67c31cc6373db2f3744d8dc12d1a4f26b025cbb2dd50a215151",
    "posts/grocery-2023-06-14-assets/data-quality.csv": "b5e155fb2a17f0b28208f4c9f07908647b1fc0366406d54ec31feec0f5581634",
    "posts/grocery-2023-06-14-assets/analysis-metadata.json": "3bb7b9c2f724a2e60ccb2a44946b5ab7da62e656bd3f920336990b15e80629a3",
}
unexpected = []
for path in root.rglob("*"):
    if path.is_symlink():
        unexpected.append(str(path.relative_to(root)))
        continue
    if not path.is_file():
        continue
    rel = path.relative_to(root)
    name = rel.as_posix()
    if name in grocery_assets and hashlib.sha256(path.read_bytes()).hexdigest() != grocery_assets[name]:
        unexpected.append(f"{name} (content does not match approved export)")
        continue
    valid = (
        name in pages
        or name in grocery_assets
        or (rel.parts[0] == "site_libs" and path.suffix.lower() in asset_types)
        or (len(rel.parts) == 2 and rel.parts[0] == "posts" and path.suffix == ".html")
        or (len(rel.parts) >= 2 and rel.parts[0] == "figures" and path.suffix.lower() in figure_types)
    )
    if not valid:
        unexpected.append(name)
if unexpected:
    sys.exit("Refusing to publish unexpected output files:\n" + "\n".join(sorted(unexpected)))
print("Deployment artifact contains only allowed site outputs.")
