
echo '🔐 GitHub VS Code Login - Quick Fix'
echo '=================================='
echo 
echo '🎯 Method 1: Personal Access Token (RECOMMENDED)'
echo '1. Go to: https://github.com/settings/tokens'
echo '2. Generate new token (classic)'
echo '3. Select: repo, user:email, read:org'
echo '4. Copy token'
echo '5. VS Code: Ctrl+Shift+P -> GitHub: Sign in -> Sign in with token'
echo
echo '🔑 Method 2: SSH Key (for long-term use)'
echo '1. ssh-keygen -t ed25519 -C "your-email@example.com"'
echo '2. eval "$(ssh-agent -s)"'
echo '3. ssh-add ~/.ssh/id_ed25519'
echo '4. cat ~/.ssh/id_ed25519.pub  # Copy to GitHub settings/ssh'
echo '5. Test: ssh -T git@github.com'
echo
echo '🌐 Method 3: Browser Fallback'
echo '1. VS Code: Ctrl+Shift+P -> GitHub: Sign in -> Sign in with browser'
echo '2. If browser doesnt open, copy URL and open on phone/other device'
echo
echo '🎉 Expected result: GitHub account appears in VS Code corner'
EOF && chmod +x github_login_quick.sh && echo '✅ Quick reference script created!'
