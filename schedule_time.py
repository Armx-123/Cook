import os
import base64
from datetime import datetime, timezone
from random import randint as r
from github import Github, Auth
from github.GithubException import UnknownObjectException

# ============================ CONFIG ============================
GITHUB_TOKEN = os.environ.get("GIT") 
REPO_NAME = "Armx-123/Cook"
BRANCH = "main"

# The file containing the keyword lines to be divided
DATA_FILE = "Data/Final_Strategy/Food_And_Drinks/keyword_bank.txt"

# Offset configuration to prevent API rate limits. 
# "use_remainder" dictates if this specific workflow gets the extra posts.
WORKFLOW_CONFIG = {
    "Post.yml":   {"offset": 0,  "use_remainder": False},
    "Videos.yml": {"offset": 5,  "use_remainder": False},
    "E_Books.yml":{"offset": 10, "use_remainder": True}
}
# ===============================================================

def calculate_todays_schedules(filepath, use_remainder):
    """Calculates how many posts should be scheduled strictly for TODAY."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            total_lines = sum(1 for line in f if line.strip())
            
        base_count = total_lines // 7
        remainder = total_lines % 7
        
        # ISO Weekday: 1 = Monday, 2 = Tuesday ... 7 = Sunday
        current_day = datetime.now(timezone.utc).isoweekday()
        
        # If this workflow uses remainders, and today falls within the remainder distribution
        if use_remainder and current_day <= remainder:
            todays_total = base_count + 1
            print(f"📊 Today gets an extra post! (Base {base_count} + 1 Remainder)")
        else:
            todays_total = base_count
            print(f"📊 Today gets base schedules only: {base_count}")
            
        return max(1, min(todays_total, 60)) # Cap at 60 for GitHub limits
    
    except FileNotFoundError:
        print(f"⚠️ {filepath} not found. Defaulting to 1 schedule for today.")
        return 1

def generate_todays_crons(count):
    """Generates random times strictly between 01:00 and 23:59 UTC."""
    crons = []
    for _ in range(count):
        minute = r(0, 59)
        # Assuming script runs at 00:00 UTC, schedule hours 1-23 so they are in the future
        hour = r(1, 23) 
        crons.append(f"{minute} {hour} * * *")
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

def update_github_workflows(config):
    """Iterate through workflows, calculate today's count, generate times, and push."""
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)
    
    for workflow_name, settings in config.items():
        print(f"\n--- Processing {workflow_name} ---")
        workflow_path = f".github/workflows/{workflow_name}"
        
        # 1. Calculate how many posts THIS workflow needs TODAY
        todays_count = calculate_todays_schedules(DATA_FILE, settings["use_remainder"])
        
        # 2. Generate times and apply rate-limit offsets
        base_crons = generate_todays_crons(todays_count)
        final_crons = [offset_cron_time(c, settings["offset"]) for c in base_crons]
            
        try:
            workflow_file = repo.get_contents(workflow_path, ref=BRANCH)
            original_yaml = base64.b64decode(workflow_file.content).decode("utf-8")
            
            updated_yaml = inject_schedules_into_yaml(original_yaml, final_crons)
            
            if original_yaml.strip() != updated_yaml.strip():
                repo.update_file(
                    path=workflow_path,
                    message=f"🤖 Auto-update 24h schedule for {workflow_name}",
                    content=updated_yaml,
                    sha=workflow_file.sha,
                    branch=BRANCH,
                )
                print(f"✅ Updated {workflow_name} with {len(final_crons)} times for today.")
            else:
                print(f"⏩ No changes needed for: {workflow_name}")
                
        except UnknownObjectException:
            print(f"❌ Error: {workflow_name} not found in the repository!")

if __name__ == "__main__":
    update_github_workflows(WORKFLOW_CONFIG)