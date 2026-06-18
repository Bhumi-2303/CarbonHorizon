import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Backgrounds
    content = re.sub(r'bg-white\b', 'bg-deep-ocean', content)
    content = re.sub(r'bg-slate-(?:50|100|200)\b', 'bg-deep-ocean', content)
    content = re.sub(r'bg-slate-(?:800|900|950)\b', 'bg-deep-ocean', content)
    
    # 2. Text colors
    content = re.sub(r'text-slate-(?:900|800)\b', 'text-white', content)
    content = re.sub(r'text-slate-(?:400|500|600)\b', 'text-muted', content)
    content = re.sub(r'text-emerald-(?:400|500|600)\b', 'text-earth-green', content)
    content = re.sub(r'text-green-(?:400|500|600)\b', 'text-earth-green', content)

    # 3. Accents
    content = re.sub(r'bg-emerald-(?:400|500|600)\b', 'bg-earth-green', content)
    content = re.sub(r'bg-green-(?:400|500|600)\b', 'bg-earth-green', content)
    content = re.sub(r'border-emerald-(?:400|500|600)\b', 'border-earth-green', content)
    content = re.sub(r'ring-emerald-(?:400|500|600)\b', 'ring-earth-green', content)

    # Clean up opacity modifiers on replaced classes (e.g. bg-earth-green/50)
    # Actually, Earth Intelligence requires solid custom colors. Let's just remove specific old classes.
    content = re.sub(r'bg-emerald-\d+/\d+', 'bg-earth-green/20', content)
    content = re.sub(r'border-emerald-\d+/\d+', 'border-earth-green/30', content)

    # 4. Glass Cards (heuristic replacement for large containers)
    # Common old dark glass pattern: bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl
    content = re.sub(r'bg-slate-900/80\s+backdrop-blur-xl\s+border\s+border-slate-700/50\s+rounded-2xl', 'glass-card', content)
    
    # Common old light/dark card pattern: bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800
    content = re.sub(r'bg-white\s+dark:bg-slate-900\s+rounded-2xl\s+shadow-sm\s+border\s+border-slate-200\s+dark:border-slate-800', 'glass-card', content)

    # Clean up dark: prefixes for replaced colors since new design is purely dark mode
    content = re.sub(r'dark:bg-slate-\d+', 'bg-deep-ocean', content)
    content = re.sub(r'dark:text-white', 'text-white', content)
    content = re.sub(r'dark:text-slate-\d+', 'text-muted', content)
    content = re.sub(r'dark:border-slate-\d+', 'border-deep-ocean', content)

    # 5. Buttons
    # The global css handles .btn-primary and .btn-outline, but we should make sure inline classes don't conflict
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

def main():
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                process_file(os.path.join(root, file))

if __name__ == '__main__':
    main()
