
python3 -m venv app_env

# Ubuntu may require a special package (like python3.10-venv)
# before the above command will work.
if [ $? -ne 0 ]; then
    rm -rf app_env
    exit 1
fi

cd app_env

BRANCH_NAME=develop # as of 03/21/24, this is the most up-to-date branch
wget https://github.com/PacificBiosciences/pbcore/archive/refs/heads/${BRANCH_NAME}.zip
if [ $? -ne 0 ]; then
    echo "Failed to download pbcore package files."
    exit 1
fi

# Check if unzip is installed
if ! command -v unzip &> /dev/null; then
    echo "unzip is not installed"
    exit 1
fi

unzip ${BRANCH_NAME}.zip

set -e # exit if any command fails

# install required packages
bin/pip install -e pbcore-$BRANCH_NAME
bin/pip install requests
bin/pip install peewee
bin/pip install globus-sdk
bin/pip install pytest

# Check that the packages were installed
pip_output=$(bin/pip list)
grep -q "pbcore" <<< $pip_output
grep -q "requests" <<< $pip_output
grep -q "peewee" <<< $pip_output
grep -q "globus-sdk" <<< $pip_output