from github import Github
import os

# ============================ CONFIG ============================
GITHUB_TOKEN = os.environ["GIT"]
REPO_NAME = "Armx-123/Cook"
BRANCH = "main"

WORKFLOW_PATH = ".github/workflows/Post.yml"
TIMES_FILE = "times.txt"
# ===============================================================


def read_cron_times(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def generate_workflow_yaml(cron_lines):
    yaml = [
        "name: Post on Pinterest",
        "",
        "on:",
        "  workflow_dispatch:",
        "  schedule:",
    ]

    # Add every cron expression from times.txt
    for cron in cron_lines:
        yaml.append(f"    - cron: '{cron}'")

    yaml.extend([
        "",
        "jobs:",
        "  run-seo-script:",
        "    runs-on: ubuntu-latest",
        "",
        "    permissions:",
        "      contents: write",
        "",
        "    env:",
        "      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}",
        "      RYNX: ${{ secrets.RYNX }}",
        "      PINTEREST_CLIENT_ID: ${{ secrets.PINTEREST_CLIENT_ID }}",
        "      PINTEREST_CLIENT_SECRET: ${{ secrets.PINTEREST_CLIENT_SECRET }}",
        "",
        "    steps:",
        "      - name: Check out repository",
        "        uses: actions/checkout@v4",
        "",
        "      - name: Set up Python",
        "        uses: actions/setup-python@v5",
        "        with:",
        "          python-version: '3.12'",
        "",
        "      - name: Cache Hugging Face Models",
        "        uses: actions/cache@v4",
        "        with:",
        "          path: ~/.cache/huggingface",
        "          key: ${{ runner.os }}-hf-florence2",
        "          restore-keys: |",
        "            ${{ runner.os }}-hf-florence2-",
        "",
        "      - name: Install Python dependencies",
        "        run: |",
        "          python -m pip install --upgrade pip",
        "          pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu",
        "          pip install -r r.txt",
        "",
        "      - name: Install Playwright Browsers",
        "        run: |",
        "          pip install playwright",
        "          playwright install --with-deps",
        "",
        "      - name: Install OpenVPN Client Backend",
        "        run: |",
        "          sudo apt-get update",
        "          sudo apt-get install -y openvpn",
        "",
        "      - name: Run SEO Script",
        "        run: python SEO/download.py",
        "",
        "      - name: Run Main Script",
        "        run: python main.py",
    ])

    return "\n".join(yaml)


def update_github_workflow(yaml_content):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    contents = repo.get_contents(WORKFLOW_PATH, ref=BRANCH)

    repo.update_file(
        path=WORKFLOW_PATH,
        message="🤖 Auto-update workflow schedule",
        content=yaml_content,
        sha=contents.sha,
        branch=BRANCH,
    )

    print("✅ Workflow updated successfully!")


if __name__ == "__main__":
    cron_times = read_cron_times(TIMES_FILE)
    workflow = generate_workflow_yaml(cron_times)
    update_github_workflow(workflow)
