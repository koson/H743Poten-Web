#!/bin/bash

# สร้าง startup script ที่ bypass scipy
export PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH"

# Temporary fix: สร้าง symbolic link scipy
cd poten-env/lib/python3.11/site-packages/
if [ ! -d "scipy" ]; then
    ln -s /usr/lib/python3/dist-packages/scipy scipy
fi

echo "✅ Setup scipy link for virtual environment"
