"""
Extract all notetags, plugin commands, and JS capabilities from VisuStella MZ
and other RPG Maker MZ plugins. Outputs organized text files for reference.
"""
import os
import re
import json

PLUGINS_DIR = r"C:\Consilience\Consilience\js\plugins"
OUTPUT_DIR = r"C:\Consilience\scripts\plugin_extracts"

# Skip Chinese duplicate files
SKIP_PATTERNS = ["-中文.js"]

def should_skip(filename):
    for pat in SKIP_PATTERNS:
        if pat in filename:
            return True
    return False

def extract_help_section(filepath):
    """Extract the @help documentation section from a plugin file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Find @help section
    help_match = re.search(r'\*\s*@help\s*\n(.*?)(?=\n\s*\*\s*@|\*/)', content, re.DOTALL)
    if help_match:
        raw = help_match.group(1)
        # Clean up comment markers
        lines = []
        for line in raw.split('\n'):
            # Remove leading " * " comment markers
            cleaned = re.sub(r'^\s*\*\s?', '', line)
            lines.append(cleaned)
        return '\n'.join(lines)
    return ""

def extract_notetags(help_text):
    """Extract all notetag patterns from help text."""
    notetags = []
    lines = help_text.split('\n')
    in_notetag_section = False
    current_block = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect notetag sections
        if 'Notetag' in stripped and '===' in stripped:
            in_notetag_section = True
            continue

        # Detect notetag lines (lines starting with <)
        if re.match(r'^<[^>]+>', stripped):
            current_block.append(stripped)
            # Collect context lines after
            for j in range(i+1, min(i+10, len(lines))):
                ctx = lines[j].strip()
                if ctx.startswith('<') or ctx == '---' or ctx == '':
                    break
                current_block.append(ctx)
            if current_block:
                notetags.append('\n'.join(current_block))
                current_block = []

    return notetags

def extract_plugin_commands(help_text):
    """Extract plugin command documentation."""
    commands = []
    lines = help_text.split('\n')
    in_cmd_section = False
    current_cmd = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if 'Plugin Commands' in stripped and '===' in stripped:
            in_cmd_section = True
            continue
        if in_cmd_section and '===' in stripped and 'Plugin Commands' not in stripped:
            # New major section, stop
            if current_cmd:
                commands.append('\n'.join(current_cmd))
                current_cmd = []
            in_cmd_section = False
            continue
        if in_cmd_section:
            current_cmd.append(line)

    if current_cmd:
        commands.append('\n'.join(current_cmd))

    return commands

def extract_plugin_command_defs(filepath):
    """Extract @command definitions from plugin file header."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Find all @command definitions in the plugin header
    header_match = re.search(r'/\*:(.*?)\*/', content, re.DOTALL)
    if not header_match:
        return []

    header = header_match.group(1)
    commands = []

    # Find @command entries
    cmd_pattern = re.compile(
        r'@command\s+(\S+).*?'
        r'(?:@text\s+(.*?))?'
        r'(?:@desc\s+(.*?))?'
        r'((?:\s*@arg\s+.*?)*)',
        re.DOTALL
    )

    # Simpler approach: find all @command lines
    cmd_lines = []
    for line in header.split('\n'):
        cleaned = re.sub(r'^\s*\*\s?', '', line)
        cmd_lines.append(cleaned)

    current_command = None
    results = []

    for line in cmd_lines:
        stripped = line.strip()
        if stripped.startswith('@command '):
            if current_command:
                results.append(current_command)
            current_command = {'command': stripped.replace('@command ', ''), 'text': '', 'desc': '', 'args': []}
        elif current_command:
            if stripped.startswith('@text '):
                current_command['text'] = stripped.replace('@text ', '')
            elif stripped.startswith('@desc '):
                current_command['desc'] = stripped.replace('@desc ', '')
            elif stripped.startswith('@arg '):
                current_command['args'].append(stripped.replace('@arg ', ''))

    if current_command:
        results.append(current_command)

    return results

def extract_js_evals(help_text):
    """Extract JavaScript/code eval sections from help text."""
    js_sections = []
    lines = help_text.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for JS: sections, code sections, Lunatic Mode, etc.
        if any(kw in stripped for kw in ['JavaScript', 'Script Call', 'Lunatic Mode', 'JS:', 'code']):
            if '===' in stripped or '---' in stripped:
                block = [stripped]
                for j in range(i+1, min(i+50, len(lines))):
                    ctx = lines[j].strip()
                    if '===' in ctx and j > i+1:
                        break
                    block.append(lines[j])
                js_sections.append('\n'.join(block))

    return js_sections

def process_plugin(filepath, filename):
    """Process a single plugin file and return extracted data."""
    result = {
        'filename': filename,
        'help_text': '',
        'notetags': [],
        'plugin_commands_doc': [],
        'plugin_command_defs': [],
        'js_evals': [],
    }

    help_text = extract_help_section(filepath)
    result['help_text'] = help_text
    result['notetags'] = extract_notetags(help_text)
    result['plugin_commands_doc'] = extract_plugin_commands(help_text)
    result['plugin_command_defs'] = extract_plugin_command_defs(filepath)
    result['js_evals'] = extract_js_evals(help_text)

    return result

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(PLUGINS_DIR))
    files = [f for f in files if f.endswith('.js') and not should_skip(f)]

    print(f"Processing {len(files)} plugin files...")

    all_results = []

    for fname in files:
        fpath = os.path.join(PLUGINS_DIR, fname)
        print(f"  Processing: {fname}")
        result = process_plugin(fpath, fname)
        all_results.append(result)

        # Save individual help text
        if result['help_text']:
            safe_name = fname.replace('.js', '.txt')
            with open(os.path.join(OUTPUT_DIR, safe_name), 'w', encoding='utf-8') as f:
                f.write(f"=== {fname} ===\n\n")
                f.write(result['help_text'])

    # Save summary
    with open(os.path.join(OUTPUT_DIR, '_summary.json'), 'w', encoding='utf-8') as f:
        summary = []
        for r in all_results:
            summary.append({
                'filename': r['filename'],
                'help_length': len(r['help_text']),
                'notetag_count': len(r['notetags']),
                'plugin_cmd_count': len(r['plugin_command_defs']),
                'js_eval_count': len(r['js_evals']),
            })
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Save all help texts concatenated for reference
    with open(os.path.join(OUTPUT_DIR, '_all_help.txt'), 'w', encoding='utf-8') as f:
        for r in all_results:
            if r['help_text']:
                f.write(f"\n{'='*80}\n")
                f.write(f"=== {r['filename']} ===\n")
                f.write(f"{'='*80}\n\n")
                f.write(r['help_text'])
                f.write('\n')

    # Print stats
    total_notetags = sum(len(r['notetags']) for r in all_results)
    total_cmds = sum(len(r['plugin_command_defs']) for r in all_results)
    total_help = sum(len(r['help_text']) for r in all_results)

    print(f"\nDone!")
    print(f"  Plugins processed: {len(all_results)}")
    print(f"  Total help text: {total_help:,} chars")
    print(f"  Total notetag blocks: {total_notetags}")
    print(f"  Total plugin commands: {total_cmds}")
    print(f"  Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
