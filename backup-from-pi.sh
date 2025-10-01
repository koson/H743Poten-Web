#!/bin/bash
# Automated backup script for CV Web API from Raspberry Pi
# Usage: ./backup-from-pi.sh

set -e

echo "🔄 CV Web API Backup Script"
echo "================================"

# Configuration
PI_HOST="ben@192.168.9.75"
PI_PATH="~/cv-api"
LOCAL_DIR="CVWebAPI-CSharp"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="cv-api-backup-${TIMESTAMP}.tar.gz"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📦 Creating backup on Raspberry Pi...${NC}"
ssh ${PI_HOST} "cd ${PI_PATH} && tar czf /tmp/${BACKUP_FILE} \
    --exclude='bin' \
    --exclude='obj' \
    --exclude='*.log' \
    --exclude='nohup.out' \
    --exclude='*.tar.gz' \
    Program.cs CVWebApi.csproj wwwroot/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup created on Pi${NC}"
else
    echo -e "${RED}❌ Failed to create backup${NC}"
    exit 1
fi

echo -e "${YELLOW}📥 Downloading backup...${NC}"
scp ${PI_HOST}:/tmp/${BACKUP_FILE} /tmp/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup downloaded${NC}"
else
    echo -e "${RED}❌ Failed to download backup${NC}"
    exit 1
fi

echo -e "${YELLOW}📂 Extracting to ${LOCAL_DIR}...${NC}"
cd "$(dirname "$0")"
mkdir -p ${LOCAL_DIR}
cd ${LOCAL_DIR}

# Backup existing files first
if [ -f "Program.cs" ]; then
    cp Program.cs "Program.cs.backup-${TIMESTAMP}"
fi

# Extract
tar xzf /tmp/${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Extracted successfully${NC}"
else
    echo -e "${RED}❌ Failed to extract${NC}"
    exit 1
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
rm /tmp/${BACKUP_FILE}
ssh ${PI_HOST} "rm /tmp/${BACKUP_FILE}"

# Git status
cd ..
echo -e "${YELLOW}📊 Git status:${NC}"
git status --short ${LOCAL_DIR}/

# Show changes
echo ""
echo -e "${GREEN}✅ Backup completed!${NC}"
echo ""
echo "📁 Files updated:"
ls -lh ${LOCAL_DIR}/*.cs ${LOCAL_DIR}/*.csproj 2>/dev/null || true
echo ""
echo "📝 Next steps:"
echo "  1. Review changes: git diff ${LOCAL_DIR}/"
echo "  2. Test locally if needed"
echo "  3. Commit: git add ${LOCAL_DIR}/ && git commit -m 'chore: sync from Pi'"
echo "  4. Push: git push"
echo ""
echo "================================"
