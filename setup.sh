#!/bin/bash
# if [ $# -eq 0 ]; then
#     wget "https://smarslab-files.s3.amazonaws.com/epic-utils/epic_pkg.zip"
# else
#     wget -P $1 "https://smarslab-files.s3.amazonaws.com/epic-utils/epic_pkg.zip"
#     cd $1
# fi

wget -O epic_pkg.zip https://github.com/smarsGroup/EPIC-pkg/archive/master.zip

if command -v unzip &>/dev/null; then
    unzip ./epic_pkg.zip
else
    if grep -qi "ubuntu" /etc/os-release ; then
        sudo apt-get install unzip
    else
        sudo yum install unzip
    fi
    unzip ./epic_pkg.zip
fi

# Detect the path to the default Python interpreter
interpreter_path=$(which python)

if [ -z "$interpreter_path" ]; then
    echo "Error: Python interpreter not found."
    exit 1
fi

# Update the shebang line of scripts in the scripts directory
cd ./epic_pkg
script="$(pwd)/epic_lib/dispatcher.py"
echo "#!$interpreter_path" | cat - "$script" > temp && mv temp "$script"
chmod +x "$script"


wrapper_script="$(pwd)/epic_lib/scripts/epic_pkg"
echo '#!/bin/bash' > "$wrapper_script"
echo $script' "$@" ' >> "$wrapper_script"
chmod +x "$wrapper_script"

# Install Python dependencies
pip install -r requirements.txt

# Determine if the terminal is bash
if [ "$SHELL" = "/bin/bash" ] || [ "$0" = "bash" ]; then
    echo 'export PATH=$PATH:'$(pwd)/epic_lib/scripts >> ~/.bashrc
    echo "Setup for Bash complete!"
else
    echo "You are using shell: $SHELL. Please add the path $(pwd)/epic_lib/scripts to your PATH."
fi

echo "Restart your terminal or source your profile for the changes to take effect!"
