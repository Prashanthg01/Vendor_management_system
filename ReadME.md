# Vendor Management System

This is a Django-based Vendor Management System with performance metrics.

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

## API Endpoints

- Vendors: `/api/vendors/`
- Purchase Orders: `/api/purchase_orders/`
- Historical Performance: `/api/historical_performance/`

## Running Tests

To run the test suite, use the following command: