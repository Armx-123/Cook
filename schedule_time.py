import os
import base64
from random import randint as r
from github import Github, Auth
from github.GithubException import UnknownObjectException

# ============================ CONFIG ============================
GITHUB_TOKEN = os.environ.get("GIT") 
REPO_NAME = "Armx-123/Cook"
BRANCH = "main"
DATA_FILE = "Data/Final_Strategy/Food_And_Drinks/keyword_bank.txt"

# Configuration dictionary replacing the need for an external JSON.
# offset: Minutes to offset the time to prevent GitHub/API rate limits.
# use_remainder: Boolean deciding if this workflow gets the extra day-specific crons.
WORKFLOW_CONFIG = {
    "Post.yml":   {"offset": 0,  "use_remainder": False},
    "Videos.yml": {"offset": 5,  "use_remainder": False},
    "E_Books.yml":{"offset": 10, "use_remainder": True}
}
# ===============================================================

def get_schedule_counts(filepath):
    """Calculate the base daily schedules and the remainder."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = sum(1 for line in f if line.strip())
            
        base_count = lines // 7
        remainder = lines % 7
        
        print(f"📄 Found {lines} lines.")
        print(f"📊 Base daily schedules: {base_count}")
        print(f"📊 Remainder schedules: {remainder}")
        
        return base_count, remainder
    
    except FileNotFoundError:
        print(f"⚠️ {filepath} not found. Defaulting to 1 base schedule, 0 remainder.")
        return 1, 0

def generate_base_crons(count):
    """Generate daily cron times (* * *)."""
    crons = []
    # Cap base schedules at 50 to leave room for remainders without hitting GitHub's 60 limit
    count = max(1, min(count, 50))
    for _ in range(count):
        minute = r(0, 59)
        hour = r(0, 22)
        crons.append(f"{minute} {hour} * * *")
    return crons

def generate_remainder_crons(remainder):
    """Generate day-specific cron times starting from Monday (1)."""
    crons = []
    # Remainder will logically never exceed 6 (since modulo 7 maxes at 6).
    for day in range(1, remainder + 1):
        minute = r(0, 59)
        hour = r(0, 22)
        # format: minute hour day_of_month month day_of_week
        crons.append(f"{minute} {hour} * * {day}")
    return crons

def offset_cron_time(cron_str, offset_minutes):
    """Adds a minute offset to a cron string to prevent concurrent API rate limits."""
    parts = cron_str.split(" ")
    minute = int(parts[0])
    hour = int(parts[1])
    
    minute += offset_minutes
    if minute > 59:
        minute -= 60
        hour = (hour + 1) % 24
        
    return f"{minute} {hour} {parts[2]} {parts[3]} {parts[4]}"

def inject_schedules_into_yaml(original_yaml, new_crons):
    """Safely replaces the schedule block while preserving the rest of the YAML."""
    lines = original_yaml.splitlines()
    out_lines = []
    skip_mode = False
    
    for line in lines:
        if line.strip() == "schedule:":
            out_lines.append(line)
            for cron in new_crons:
                out_lines.append(f"    - cron: '{cron}'")
            out_lines.append("")
            skip_mode = True
            continue
        
        if skip_mode:
            if line.strip() == "jobs:":
                skip_mode = False
                out_lines.append(line)
            continue
        
        out_lines.append(line)
        
    return "\n".join(out_lines)

def update_github_workflows(config, base_crons, remainder_crons):
    """Iterate through the configured files, apply logic, and push."""
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)
    
    for workflow_name, settings in config.items():
        workflow_path = f".github/workflows/{workflow_name}"
        offset = settings["offset"]
        
        # 1. Apply offsets to base crons
        final_crons = [offset_cron_time(c, offset) for c in base_crons]
        
        # 2. If eligible, append the remainder crons (with the same offset)
        if settings["use_remainder"] and remainder_crons:
            final_crons.extend([offset_cron_time(c, offset) for c in remainder_crons])
            
        try:
            workflow_file = repo.get_contents(workflow_path, ref=BRANCH)
            original_yaml = base64.b64decode(workflow_file.content).decode("utf-8")
            
            updated_yaml = inject_schedules_into_yaml(original_yaml, final_crons)
            
            if original_yaml.strip() != updated_yaml.strip():
                repo.update_file(
                    path=workflow_path,
                    message=f"🤖 Auto-update schedule for {workflow_name}",
                    content=updated_yaml,
                    sha=workflow_file.sha,
                    branch=BRANCH,
                )
                print(f"✅ Updated {workflow_name} with {len(final_crons)} total schedules.")
            else:
                print(f"⏩ No changes needed for: {workflow_name}")
                
        except UnknownObjectException:
            print(f"❌ Error: {workflow_name} not found in the repository!")

def main():
    base_count, remainder = get_schedule_counts(DATA_FILE)
    
    base_crons = generate_base_crons(base_count)
    remainder_crons = generate_remainder_crons(remainder) if remainder > 0 else []
    
    update_github_workflows(WORKFLOW_CONFIG, base_crons, remainder_crons)

if __name__ == "__main__":
    main()
