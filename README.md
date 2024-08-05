# Migration Runner

## Using on VM

```bash
ssh support@webapp

cd /home/support/migration_runner

docker pull ghcr.io/mishanianod/migration-runner:latest

docker compose down

docker compose up -d

# Open http://webapp:5001 http://webapp:5002 http://webapp:5003

```
## Development

```
git clone git@github.com:mishanianod/migrationRunner.git

python -m venv venv

sournce ./venv/bin/activate

pip install -r requirements.txt

python main.py

```
