# Homepage publication assets and metrics

The selected papers are maintained in `_data/publications.json` and rendered by
`_includes/home/paper.html`.

## Added paper figures

These PNGs are direct, high-resolution crops of the public arXiv PDFs, excluding
the surrounding page text and captions. Existing illustrations were retained.

| Asset | Public paper | Figure | PDF page |
| --- | --- | --- | --- |
| `hopd-figure-1.png` | https://arxiv.org/abs/2611.25391 | 1 | 1 |
| `sarvia-figure-1.png` | https://arxiv.org/abs/2611.22273 | 1 | 1 |
| `vitp-figure-1.png` | https://arxiv.org/abs/2509.17562 | 1 | 1 |
| `languagepivot-figure-1.png` | https://arxiv.org/abs/2603.01758 | 1 | 1 |
| `sliprs-figure-1.png` | https://arxiv.org/abs/2605.23144 | 1 | 1 |
| `densevlm-figure-2.png` | https://arxiv.org/abs/2412.06244 | 2 | 2 |

## Dynamic publication badges

- GitHub stars use the corresponding repository's Shields.io badge, linked to
  that repository. The SGE code link is explicitly labeled as a mirror because
  its original `implus/PytorchInsight` URL is unavailable.
- `google_scholar_crawler/refresh.py` fetches the public Google Scholar profile
  and matches publications by Scholar ID, falling back to normalized titles.
- The data publisher writes `metrics.json` and `badges/*.json` endpoints to the
  `google-scholar-stats` branch. The manual `Get Citation Data` workflow is
  retained, but Scholar currently rejects hosted-runner requests with HTTP 403.
  Its schedule is disabled to avoid repeated failed jobs.
- `update-local.mjs` refreshes and publishes the same data using the device's
  network. It takes absolute paths to a Python executable and a clean checkout
  of the citation-data branch. A device schedule can run this command once the
  owner selects that update method.
- Citation badges link to each paper's Scholar entry; papers not yet indexed
  link to a title search and show `pending`, never an invented zero.
- Shields.io caches the badge responses. Scholar updates and GitHub scheduling
  can also introduce delays; these are automatically refreshed counts rather
  than guaranteed instantaneous values.
- If Scholar returns a challenge or incomplete response, the workflow fails
  before publication and retains the last successful data.

The crawler uses the Python standard library and requires no API key. Run a
manual refresh with `python google_scholar_crawler/refresh.py --output results`.
