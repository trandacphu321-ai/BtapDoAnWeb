import os
import re

template_dir = r"e:\MobileStore V4 _ SuaDoi\MobileStore-TTCN-FlaskPython\shop\templates"

# This regex matches: url_for('static', filename='images/' + variable)
# and url_for('static', filename='images/' ~ variable)
# and url_for('static',filename='images/'+variable)
pattern = re.compile(r"url_for\('static'\s*,\s*filename='images/'\s*[+~]\s*([^)]+)\)")

count = 0
for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith(".html"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = pattern.sub(r"\1 | firebase_image", content)
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
                count += 1

print(f"Total files updated: {count}")
