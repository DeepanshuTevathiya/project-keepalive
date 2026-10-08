# Project Keepalive

This repository periodically opens deployed Streamlit apps and Hugging Face Spaces so that sleeping demos can be woken up.

## Add a project

Edit [`projects.json`](projects.json) and add an object with:

- `name`: a label printed in the workflow log
- `url`: the deployed app or Space URL
- `type`: either `streamlit` or `huggingface`

For example:

```json
{
  "name": "My demo",
  "url": "https://example.com",
  "type": "streamlit"
}
```

Commit and push the change. The scheduled workflow will include the new project on its next run.

## Run locally

Install the Python dependency and Chromium once:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Then run:

```bash
python keepalive.py
```

Each project gets up to two retries after its initial attempt. The script checks every project and exits non-zero if any project fails.

## Run manually on GitHub

Open the repository's **Actions** tab, choose **Keep demo apps awake**, click **Run workflow**, select the branch, and click **Run workflow** again. The workflow also runs automatically every six hours.
