# main.py
import datetime
import json
from pydantic import BaseModel
from fastapi import FastAPI
import numpy as np


app = FastAPI()

class CalculateChargePrice(BaseModel):
    customerId: int
    start_date: str
    end_date: str


# List of out company provided services. 
# This information should perhaps be fetched from another db microservice
company_provided_services = [{"name": "A", "price": 0.2, "workingDays": True},
                             {"name": "B", "price": 0.24, "workingDays": True},
                             {"name": "C", "price": 0.4, "workingDays": False}]


# Using a json file as a "fake database".
# This information should perhaps be fetched from another db microservice
with open('data.json', "r") as f:
    customerData = json.load(f)['Customers']
# print(customerData)
f.close()


@app.post('/')
def get_charge_price(calculateChargePrice: CalculateChargePrice):
    # Assuming the ID of the customer to be unique
    customer = [c for c in customerData if c['id'] == calculateChargePrice.customerId]
    # print(customer)

    if len(customer) > 0:
        # Convert the start_date and end_date from the query to datetime objects
        start_date_obj = convertToDatetimeObject(calculateChargePrice.start_date)
        end_date_obj = convertToDatetimeObject(calculateChargePrice.end_date)

        # If either of them isn't provided return a response telling that there are missing values
        if start_date_obj is None or end_date_obj is None:
            return {"message": "Missing start_date or end_date in query"}

        # If the start_date query value is larger than end_date
        # Ex: start_date: 2019-01-09, end_date: 2019-01-08 
        if start_date_obj > end_date_obj:
            print("The sent in start_date is after the end_date: start_date: " + str(start_date_obj) + " end_date: " + str(end_date_obj))
            return 0

        total_cost = calculate_total_cost(customer[0], start_date_obj, end_date_obj)
        return round(total_cost, 3)
    else:
        return {"message": "Found no customer with ID: " + str(calculateChargePrice.customerId)}


# Calculates the total amount to charge towards a company
def calculate_total_cost(customer, start_date_obj: datetime, end_date_obj: datetime):
    total_cost = 0
    if len(customer['services']) > 0:
        for service in customer['services']:
            total_cost += calculate_service_specific_cost(customer, service, start_date_obj, end_date_obj)
    return total_cost


def calculate_service_specific_cost(customer, service, start_date_obj: datetime, end_date_obj: datetime):
    # Get the base values from the global variable company_provided_services
    # To be used if no specific prices has been set on the services and the base ones should be used, also checks which days to charge for a service
    service_base_values = [s for s in company_provided_services if s['name'] == service['name']]

    # If the service is not a service listed in our "provided services" list. Service does not exists return cost = 0.
    if len(service_base_values) <= 0:
        print("The service, " + service['name'] + ", we try to charge for does not exists in our provided services list")
        return 0

    # Check if a start_date is set for the service
    if 'start_date' in service:
        service_start_date = convertToDatetimeObject(service['start_date'])
        # The service should not be charged between the given query interval since the service_start_date is after end_date in query
        if service_start_date > end_date_obj:
            return 0
        # The service should be charged from the value in service_start_date not from the start_date value in query
        if service_start_date > start_date_obj:
            start_date_obj = service_start_date


    # Apply potential freedays to the start_date_obj
    start_date_obj = apply_freedays(customer, start_date_obj)
    if start_date_obj > end_date_obj:
        print("After applying freedays the start_date is 'larger' than the end_date, nothing to charge")
        return 0

    # Check how many days we should charge the service for
    days_to_charge = get_amount_of_days_to_charge(service_base_values, start_date_obj, end_date_obj)

    # Check if there are any discount days for the service and if so how much is it and how many days
    discount_days, discount = get_amount_of_discount_days_and_percentage(service, service_base_values, start_date_obj, end_date_obj)

    # Check if the company has a specific price, that differs from the base price, for the service.
    price_per_day = get_price_per_day(service, service_base_values)

    # Amount to pay for full price days
    full_price_days_charge = (days_to_charge - discount_days) * price_per_day

    # Amount to pay for discount price days
    discount_price_days_charge = discount_days * (discount * price_per_day)

    return full_price_days_charge + discount_price_days_charge


def get_amount_of_discount_days_and_percentage(service, service_base_values, start_date_obj, end_date_obj):
    if 'discount' not in service:
        # No discount days and no percentage
        return 0, 0
    
    # Convert it to a datetime object
    discount_start_date_obj = convertToDatetimeObject(service['discount']['start_date'])
    # Ex: 2018-07-20 > 2018-01-01. Should do the calculation from 2018-07-20.
    # This might be the case if the customer has free days.
    if start_date_obj > discount_start_date_obj:
        discount_start_date_obj = start_date_obj

    # If there isn't a provided end_date for the discount 
    # we assume that the discount is applicable for the rest of the time(Up until the given end_date in the query)
    if 'end_date' not in service['discount']:
        discount_end_date_obj = end_date_obj
    else:
        discount_end_date_obj = convertToDatetimeObject(service['discount']['end_date'])
        if discount_end_date_obj > end_date_obj:
            discount_end_date_obj = end_date_obj

    value = get_amount_of_days_to_charge(service_base_values, discount_start_date_obj, discount_end_date_obj)
    return value, (1 - service['discount']['percentage'] / 100)


def get_amount_of_days_to_charge(service_base_values, start_date_obj: datetime, end_date_obj: datetime):
    # Check if we should only charge this service for the amount of working days(Mon-Fri), else charge for full week(Mon-Sun)
    if service_base_values[0]['workingDays']:
        amount_of_days_to_charge = calculate_amount_of_weekdays(start_date_obj, end_date_obj)
    else:
        # Add one day to include the "end_date"
        amount_of_days_to_charge = (end_date_obj - start_date_obj).days + 1
    return amount_of_days_to_charge


def calculate_amount_of_weekdays(start_date_obj: datetime, end_date_obj: datetime):
    busydays = np.busday_count(start_date_obj.strftime('%Y-%m-%d'), end_date_obj.strftime('%Y-%m-%d'))
    
    # np.busday_count exlcudes the end_date. Have to doublecheck if it is a weekday or not.
    if end_date_obj.weekday() < 5: # 0 Mon, 1 Tue, 2 Wed, 3 Thur, 4 Fri
        busydays += 1
    
    return busydays


# Apply potential freedays to the start_date_obj
def apply_freedays(customer, start_date_obj):
    if 'freedays' in customer:
        start_date_obj = start_date_obj + datetime.timedelta(days=customer['freedays'])
    return start_date_obj


# Get the price the customer should pay for this service per day
def get_price_per_day(service, service_base_values):
    if "price" in service:
        return service['price']
    else:
        return service_base_values[0]['price']
 
# Convert a string to a datetime object
def convertToDatetimeObject(date):
    if date is not None:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    return date
