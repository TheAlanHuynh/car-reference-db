# car-reference-db

Reference database and evaluator for used cars in Canada

# 1 Clone and enter the repo

git clone https://github.com/TheAlanHuynh/car-reference-db
cd car-reference-db

# 2 Create & activate a virtual-env (example for Windows • PowerShell)

python -m venv venv
venv\Scripts\activate

# 3 Install server + tooling

pip install -r backend/requirements.txt

# 4 Create / upgrade the SQLite schema

set FLASK_APP=backend:create_app # (use `export` on Linux/macOS)
flask db upgrade

# 5 Load the cleaned dataset (~404 k rows, 8–10 s)

python import_vehicle_data.py
