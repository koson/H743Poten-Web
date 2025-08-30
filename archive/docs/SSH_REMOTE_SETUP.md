# SSH Remote Development Setup Guide

## ✅ SSH Server Successfully Configured!

### 🌐 Connection Information
- **WSL IP Address**: `172.21.206.99`
- **Username**: `koson`
- **SSH Port**: `22`

### 📱 VS Code Remote Development Setup

#### Step 1: Install VS Code Extension
1. Open VS Code on the remote machine
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Remote - SSH" 
4. Install the extension by Microsoft

#### Step 2: Connect to WSL
1. Press `Ctrl+Shift+P` in VS Code
2. Type "Remote-SSH: Connect to Host"
3. Enter: `koson@172.21.206.99`
4. Select "Linux" as the platform
5. Enter your WSL password when prompted

#### Step 3: Open Project Folder
1. Once connected, click "Open Folder"
2. Navigate to: `/mnt/d/GithubRepos/_Poten.2025/H743Poten/H743Poten-Web`
3. Click "OK" to open the project

### 🔑 SSH Key Authentication (Recommended)

For passwordless login, set up SSH keys:

```bash
# On the remote machine (where VS Code is running):
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
ssh-copy-id koson@172.21.206.99
```

### 🚀 Quick Start Commands

#### Start SSH Server (if stopped):
```bash
cd /mnt/d/GithubRepos/_Poten.2025/H743Poten/H743Poten-Web
./start_wsl_ssh.sh
```

#### Check SSH Status:
```bash
sudo systemctl status ssh
```

#### View Current IP:
```bash
ip addr show eth0 | grep 'inet '
```

### 🛠️ Development Workflow

Once connected via VS Code Remote SSH:

1. **Install Python Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Run Peak Detection System**:
   ```bash
   python3 main.py
   ```

3. **Access Web Interface**:
   - Open browser to: `http://172.21.206.99:5000`
   - Peak Detection: `http://172.21.206.99:5000/peak_detection`

### 🔧 Troubleshooting

#### SSH Connection Refused:
```bash
sudo systemctl restart ssh
sudo systemctl enable ssh
```

#### IP Address Changed:
```bash
# Get new IP address
ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
```

#### Firewall Issues:
- Make sure Windows Firewall allows port 22
- Or disable Windows Firewall temporarily for testing

### 🎯 VS Code Remote Features

Once connected, you'll have:
- ✅ Full IntelliSense and debugging
- ✅ Integrated terminal (WSL)
- ✅ Git integration
- ✅ Extension sync
- ✅ File explorer for WSL filesystem
- ✅ Port forwarding for web development

### 📂 Project Structure Access

The project is located at:
```
/mnt/d/GithubRepos/_Poten.2025/H743Poten/H743Poten-Web/
├── src/                          # Main application code
├── templates/                    # HTML templates
├── static/                      # CSS, JS, images
├── validation_data/             # Peak detection framework
├── peak_detection.html          # Peak detection interface
├── peak_visualization.js        # Interactive visualization
└── peak_detection_framework.py  # Backend processing
```

**Ready for remote development! 🚀**
