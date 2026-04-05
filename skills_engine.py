import os
from pathlib import Path
import subprocess
import logging

log = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent / "skills"

class Skill:
    def __init__(self, name, description, arguments, content_lines):
        self.name = name
        self.description = description
        self.arguments = arguments
        self.content_lines = content_lines
        
def load_skills() -> dict[str, Skill]:
    skills = {}
    if not SKILLS_DIR.exists():
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        return skills
        
    for file in SKILLS_DIR.glob("*.md"):
        try:
            content = file.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            # Simple frontmatter parser
            if not lines or not lines[0].startswith("---"):
                continue
                
            frontmatter_end = 0
            for i in range(1, len(lines)):
                if lines[i].startswith("---"):
                    frontmatter_end = i
                    break
                    
            if frontmatter_end == 0:
                continue
                
            name = ""
            desc = ""
            args = []
            
            for line in lines[1:frontmatter_end]:
                if ":" not in line: continue
                k, v = line.split(":", 1)
                k = k.strip().lower()
                v = v.strip()
                if k == "name":
                    name = v
                elif k == "description":
                    desc = v
                elif k == "arguments":
                    args = [a.strip() for a in v.split(",") if a.strip()]
                    
            if name:
                skills[name] = Skill(name, desc, args, lines[frontmatter_end+1:])
        except Exception as e:
            log.error(f"Failed to load skill {file.name}: {e}")
            
    return skills

def get_skills_prompt() -> str:
    skills = load_skills()
    if not skills:
        return ""
        
    prompt = "You have access to the following custom Tools (Skills):\n"
    instructional_skills = []
    
    for s in skills.values():
        has_commands = any(line.strip().startswith("!") for line in s.content_lines)
        if has_commands:
            args_str = ", ".join(s.arguments)
            prompt += f"- {s.name}: {s.description}. Arguments: [{args_str}]\n"
        else:
            instructional_skills.append(s)
            
    prompt += "\nTo use a tool skill, output exactly: <use_skill name=\"SKILL_NAME\">ARGUMENT_VALUE</use_skill>. "
    prompt += "Currently, you can only pass a single flat argument string inside the tag.\n"
    
    if instructional_skills:
        prompt += "\nYou also have the following embedded knowledge/instructional skills active:\n"
        for s in instructional_skills:
            content_str = "\n".join(s.content_lines).strip()
            prompt += f"\n--- KNOWLEDGE SKILL: {s.name} ---\n{s.description}\n{content_str}\n"
            
    return prompt

def execute_skill(skill_name: str, argument_val: str) -> str:
    skills = load_skills()
    if skill_name not in skills:
        return f"Error: Skill '{skill_name}' not found."
        
    skill = skills[skill_name]
    output = []
    
    # Very simple argument substitution (replaces ${arg} with argument_val)
    # Assumes single argument for right now given XML constraints
    arg_name = skill.arguments[0] if skill.arguments else "arg"
    
    for line in skill.content_lines:
        line = line.strip()
        if line.startswith("!`"):
            # Format: !`command`
            cmd = line[2:-1]
        elif line.startswith("!"):
            # Format !command
            cmd = line[1:]
        else:
            continue
            
        cmd = cmd.replace(f"${{{arg_name}}}", argument_val)
        
        log.info("🪄 Executing skill command: %s", cmd)
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", timeout=30)
            output.append(f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        except Exception as e:
            output.append(f"Execution Error: {str(e)}")
            
    return "\n".join(output) if output else "Skill executed, but produced no terminal commands."
