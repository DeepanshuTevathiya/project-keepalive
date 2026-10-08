# Project Keepalive

This repository periodically opens deployed Streamlit apps and Hugging Face Spaces so that sleeping demos can be woken up.

## Web UI on Vercel

The repository includes a Vercel UI at the root. It reads and updates `projects.json` through the GitHub Contents API, so adding a project in the UI creates a commit that the keepalive workflow will use.

To deploy it:

1. Import this repository into Vercel.
2. Enable **Deployment Protection → All Deployments → Vercel Authentication** in the Vercel project settings. This keeps both the UI and API private.
3. Add these Vercel environment variables for Production:
   - `GITHUB_TOKEN`: a GitHub token with **Contents: Read and write** access to this repository.
   - `ADMIN_KEY`: a separate long random password used by the UI.
   - `GITHUB_REPO`: `DeepanshuTevathiya/project-keepalive` (optional; this is the default).
   - `GITHUB_BRANCH`: `main` (optional; this is the default).
4. Deploy and open the protected Vercel URL. Enter the `ADMIN_KEY` in the form when managing projects.

The browser never receives the GitHub token. The API requires the admin key, validates the project name, URL, and type, then commits the updated JSON file.

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
