#!/bin/bash

# Environment name
ENV_NAME="my_project_env"
ENV_YML="environment.yml"
ANACONDA_INSTALLER="Anaconda3-latest-Linux-x86_64.sh"
ANACONDA_URL="https://repo.anaconda.com/archive/$ANACONDA_INSTALLER"

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
    if [[ -f "$ENV_YML" ]]; then
        echo "Creating Conda environment '$ENV_NAME' from '$ENV_YML'..."
        conda env create -f "$ENV_YML"
    else
        echo "Environment file '$ENV_YML' not found. Please ensure the file exists."
        exit 1
    fi
}

# Main script
# 1. Check if Conda is installed
check_conda_installed

# 2. Check if the environment exists, if not create it
if ! check_env_exists; then
    create_env
fi

# 3. Activate the environment
echo "Activating environment '$ENV_NAME'..."
conda activate "$ENV_NAME"
echo "Environment '$ENV_NAME' is activated."
