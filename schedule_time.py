from github import Github
import os

# ============================ CONFIG ============================
GITHUB_TOKEN = os.environ['GIT'] # Or paste your token directly (not recommended)
REPO_NAME = "Armx-123/instagram-meme"  # Format: user/repo
BRANCH = "main"
WORKFLOW_PATH = ".github/workflows/Upload.yml"
TIMES_FILE = "times.txt"
# ==============================================================


def read_cron_times(filepath):
    with open(filepath, "r") as f:
        lines = f.read().strip().splitlines()
    return lines


def generate_workflow_yaml(cron_lines):
    indent = " " * 4
    lines = [
        "name: Upload",
        "",
        "on:",
        "  schedule:",
    ]
    for cron in cron_lines:
        lines.append(f"{indent}- cron: \"{cron}\"")
    lines.append("  workflow_dispatch:")
    lines.append("")
    lines.append("env:")
    lines.append("  ACTIONS_ALLOW_UNSECURE_COMMANDS: true")
    lines.append("  RYNX: ${{ secrets.RYNX }}")
    lines.append("  CYBRIX: ${{ secrets.CYBRIX }}")
    lines.append("")
    lines.extend([
        "jobs:",
        "  scrape-latest:",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - name: Checkout repo",
        "        uses: actions/checkout@v2",
        "",
        "      - name: Setup FFmpeg",
        "        uses: federicocarboni/setup-ffmpeg@v3.1",
        "",
        "      - name: Set up Python",
        "        uses: actions/setup-python@v3",
        "        with:",
        "          python-version: '3.12.2'",
        "",
        "      - name: Install requirements",
        "        run: pip install -r r.txt",
        "",
        "      - name: Test env vars for python",
        "        run: TEST_SECRET=${{ secrets.RYNX }}",
        "",
        "      - name: Download",
        "        run: python download.py",
        "",
        "      - name: Process",
        "        run: python post_main.py"
    ])
    return "\n".join(lines)


def update_github_workflow(yaml_content):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(WORKFLOW_PATH, ref=BRANCH)

    repo.update_file(
        path=WORKFLOW_PATH,
        message="🛠️ Auto-update upload.yml from script",
        content=yaml_content,
        sha=contents.sha,
        branch=BRANCH
    )
    print("✅ upload.yml successfully pushed to GitHub!")


# ========== MAIN ==========
if __name__ == "__main__":
    cron_times = read_cron_times(TIMES_FILE)
    new_yaml = generate_workflow_yaml(cron_times)
    update_github_workflow(new_yaml)
