python3 -m venv app_env

# Ubuntu may require a special package (like python3.10-venv)
# before the above command will work.
if [ $? -ne 0 ]; then
    rm -rf app_env
    exit 1
fi

cd app_env
wget https://github.com/PacificBiosciences/pbcore/releases/download/2.1.2/pbcore-2.1.2.tar.gz

tar -xvzf pbcore-2.1.2.tar.gz

bin/pip install -e pbcore-2.1.2
bin/pip install requests
bin/pip install peewee
bin/pip install globus-sdk