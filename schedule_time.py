from github import Github, Auth
import os

# ============================ CONFIG ============================
GITHUB_TOKEN = os.environ["GIT"]  # Personal Access Token
REPO_NAME = "Armx-123/Cook"
BRANCH = "main"

WORKFLOW_PATH = ".github/workflows/Post.yml"
TIMES_FILE = "times.txt"
# ===============================================================


def read_cron_times(filepath):
    """Read cron expressions from times.txt"""
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def generate_workflow_yaml(cron_lines):
    """Generate the workflow YAML with schedules from times.txt"""

    yaml = [
        "name: Post on Pinterest",
        "",
        "on:",
        "  workflow_dispatch:",
        "  schedule:",
    ]

    # Add all cron schedules
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
    """Update the workflow file in GitHub"""

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)

    repo = g.get_repo(REPO_NAME)
    user = g.get_user()
    print(user.login)
    print(f"Connected to: {repo.full_name}")
    print(f"Default branch: {repo.default_branch}")

    # Show available workflow files (debug)
    print("\nWorkflow files:")
    workflow_files = repo.get_contents(".github/workflows", ref=BRANCH)
    for f in workflow_files:
        print(f" - {f.path}")

    # Get the existing workflow file
    workflow_file = repo.get_contents(WORKFLOW_PATH, ref=BRANCH)
    
    # Update it
    repo.update_file(
        path=WORKFLOW_PATH,
        message="🤖 Auto-update workflow schedule",
        content=yaml_content,
        sha=workflow_file.sha,
        branch=BRANCH,
    )

    print("\n✅ Workflow updated successfully!")


def main():
    cron_times = read_cron_times(TIMES_FILE)

    if not cron_times:
        raise ValueError("times.txt is empty!")

    workflow_yaml = generate_workflow_yaml(cron_times)
    update_github_workflow(workflow_yaml)


if __name__ == "__main__":
    main()
