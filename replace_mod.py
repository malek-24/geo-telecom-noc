import os

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    # Replacements
    # We replace 'moderateur_noc' with 'ingenieur_reseau' for permissions
    new_content = content.replace("moderateur_noc", "ingenieur_reseau")
    new_content = new_content.replace("'moderateur'", "'ingenieur'")
    new_content = new_content.replace('"moderateur"', '"ingenieur"')
    new_content = new_content.replace("Modérateur NOC", "Ingénieur Réseau")
    new_content = new_content.replace("Modérateur", "Ingénieur")
    new_content = new_content.replace("moderateur / mod123", "ingenieur / ing123")

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

def scan_dir(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.js') or file.endswith('.jsx') or file.endswith('.py'):
                replace_in_file(os.path.join(root, file))

scan_dir(r"c:\Users\MALEK\PROJET-TT\api")
scan_dir(r"c:\Users\MALEK\PROJET-TT\dashboard\src")
