#!/bin/bash

# Environment name
ENV_NAME="epic_env"
ENV_YML="environment.yml"
ANACONDA_INSTALLER="Anaconda3-latest-Linux-x86_64.sh"
ANACONDA_URL="https://repo.anaconda.com/archive/$ANACONDA_INSTALLER"
GITHUB_PACKAGE_URL="git+https://github.com/smarsGroup/geo-epic.git"

# Function to check if conda is installed
function check_conda_installed {
    if ! command -v conda &> /dev/null; then
        echo "Conda is not installed. Installing Anaconda..."
        install_anaconda
    else
        echo "Conda is installed."
    fi
}

# Function to install Anaconda
function install_anaconda {
    # Download Anaconda installer if not present
    if [ ! -f "$ANACONDA_INSTALLER" ]; then
        echo "Downloading Anaconda installer..."
        wget $ANACONDA_URL -O $ANACONDA_INSTALLER
    fi

    # Install Anaconda
    bash $ANACONDA_INSTALLER -b -p $HOME/anaconda3

    # Initialize Conda for the current shell
    eval "$($HOME/anaconda3/bin/conda shell.bash hook)"
    
    # Initialize Conda for future shell sessions
    conda init
    echo "Anaconda installation complete. Please restart your terminal or run 'source ~/.bashrc'."
}

# Function to check if the environment exists
function check_env_exists {
    if conda env list | grep -q "$ENV_NAME"; then
        echo "Conda environment '$ENV_NAME' already exists."
        return 0
    else
        echo "Conda environment '$ENV_NAME' does not exist."
        return 1
    fi
}

# Function to create the environment from environment.yml
function create_env {
    echo "Creating Conda environment '$ENV_NAME' ..."
    conda env create -f https://raw.githubusercontent.com/smarsGroup/geo-epic/master/environment.yml
}

# Main script
# 1. Check if Conda is installed
check_conda_installed

# 2. Check if the environment exists, if not create it
if ! check_env_exists; then
    create_env
else
    # If environment exists, install the GitHub package via pip
    echo "Updaing geo_epic package..."
    conda activate "$ENV_NAME"
    pip uninstall geo-epic
    pip install "$GITHUB_PACKAGE_URL"
    conda deactivate
fi

# 3. Activate the environment
echo "Activating environment '$ENV_NAME'..."
conda activate "$ENV_NAME"
geo_epic init
echo "Environment '$ENV_NAME' is activated."
