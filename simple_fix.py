import re

# Read the file
with open('src/routes/peak_detection.py', 'r') as f:
    content = f.read()

# Replace the problematic line pattern
old_pattern = r"if current_unit == 'ma':"
new_pattern = "current_unit_lower = current_unit.lower()\n        if current_unit_lower == 'ma':"

content = content.replace(old_pattern, new_pattern)

# Replace other patterns
content = content.replace("elif current_unit == 'na':", "elif current_unit_lower == 'na':")
content = content.replace("elif current_unit == 'a':", "elif current_unit_lower == 'a':")
content = content.replace("# For 'ua' or 'uA' - keep as is (no scaling)", "elif current_unit_lower in ['ua', 'µa']:\n            current_scale = 1.0  # microAmps - keep as is (no scaling)")

# Write back to file
with open('src/routes/peak_detection.py', 'w') as f:
    f.write(content)

print("✅ Unit header fix completed!")