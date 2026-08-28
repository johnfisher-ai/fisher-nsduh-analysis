# Social cards

Source HTML and rendered PNGs for the social preview images. Nothing here is published:
GitHub Pages serves `public/` only.

| File | Size | Used for |
|---|---|---|
| `linkedin-card.png` | 1200x627 | Open Graph image. Copied to `public/assets/img/social-card.png`, which every page references via `og:image`. Covers LinkedIn, Facebook, Slack and Twitter. |
| `github-card.png` | 1280x640 | The repository's social preview. Upload by hand under Settings > Social preview; GitHub has no API for it. |

Fill in the `{{PLACEHOLDER}}` values in each `card-*.html`, then:

```bash
bash assets/social/render.sh
```

## After changing the Open Graph image

Platforms cache previews. Re-scrape with the
[LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) or the card will keep
showing the old one, or nothing at all if the first fetch predated the image.

## If the dimensions change

`og:image:width` and `og:image:height` are written into every page. Update them together,
or the declared size will not match the file.
