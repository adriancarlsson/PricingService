# PricingService
PricingService is a Web API created with FastAPI.
It takes a customerId, start_date and end_date as input to calculate how much to charge a specific customer for. 
Currently it is using a json file containing customers as a "fake database". See `app/data.json`.

## How to use it
After starting the service(Described below) access the docs and do requests through it: `http://localhost:8000/docs`

It will calculate how much a customer with `customerId` should be charged between `start_date` and `end_date`

# Build docker image and deploy
Be in parent folder of the repo:
```sh
docker build -t pricingservice .
docker run -d --name PricingService -p 8000:8000 pricingservice
```

It should now be available through `localhost:8000`

# Setup dev environment
## Clone the repo and set up a python virtual environment
Inside the PricingService folder do:
```sh
py -3 -m venv .venv
.venv\scripts\activate
```

Sometimes windows has a restricted policy for running scripts(such as venv), temporarily allow it in the current powershell windows by: 
```sh
Set-ExecutionPolicy Unrestricted -Scope Process
```

## Get pip and install the packages defined in requirements-dev.txt
```sh 
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install -r requirements-dev.txt
```

## Run tests locally
```sh
cd app
pytest -rP
```

## Start the app locally using uvicorn
```sh
cd app
uvicorn main:app --reload
```
It will by default start up on `127.0.0.1:8000` or `localhost:8000`






