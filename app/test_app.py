from fastapi.testclient import TestClient
from .main import app
import json

client = TestClient(app)

with open('test_data.json', "r") as f:
    customerData = json.load(f)['Customers']
f.close()

def test_get_charge_price():
    for customer in customerData:
        print("\nRunning test: " + customer['name'])
        print("Testing customerId: " + str(customer['id']) + " and is expecting a total price of: " + str(customer['expectedPrice']))

        response = client.post("/", headers={"accept": "application/json", "Content-Type": "application/json"}, \
            json={"customerId": customer['id'], "start_date": customer['test_start_date'], "end_date": customer['test_end_date']},
        )

        print("Got price: " + str(response.json()))

        assert response.json()['charge_price'] == customer['expectedPrice']
        
        if 'expectedMessage' in customer:
            assert response.json()['message'] == customer['expectedMessage']