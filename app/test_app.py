from fastapi.testclient import TestClient
from .main import app
import json

client = TestClient(app)

with open('test_data.json', "r") as f:
    customerData = json.load(f)['Customers']
f.close()

def test_get_customer():
    for customer in customerData:
        print("\nRunning test: " + customer['name'])
        print("Testing customerId: " + str(customer['id']) + " and is expecting a total price of: " + str(customer['expectedPrice']))

        request = "/" + str(customer['id'])
        if "test_start_date" in customer and "test_end_date" in customer:
            request += "?start_date=" + customer['test_start_date'] + "&end_date=" + customer['test_end_date']
        elif "test_start_date" in customer:
            request += "?start_date=" + customer['test_start_date']
        else:
             request += "?end_date=" + customer['test_end_date']

        response = client.get(request)

        print("Got price: " + str(response.json()))
        
        assert response.json() == customer['expectedPrice']
        assert response.status_code == 200