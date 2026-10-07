# Smart E-Commerce Platform

## Project Overview

Smart E-Commerce Platform is a web-based e-commerce application built with Django, FastAPI and MySQL.

The platform allows customers to browse products, manage their cart, place orders and make payments. Sellers can manage products and view sales-related information. Administrators can manage users, products and orders and view analytics and reports.

## Technologies Used

- Python
- Django
- FastAPI
- MySQL
- SQLAlchemy
- HTML
- CSS
- JavaScript
- Bootstrap
- Chart.js
- Stripe Test Mode
- JWT Authentication
- Git and GitHub

## Project Structure

The project contains two main applications:

### Django Frontend

Django is used for the web interface and admin-side functionality.

Main features:
- Login and registration
- Customer dashboard
- Seller dashboard
- Admin dashboard
- Product browsing
- Cart
- Orders
- Notifications
- Profile
- CSV reports
- PDF reports

Django frontend runs on:

`http://127.0.0.1:8001/`

### FastAPI Backend

FastAPI provides the backend API and business logic.

Main features:
- User authentication
- Product management
- Cart management
- Order management
- Payment processing
- Notifications
- Profile updates

FastAPI runs on:

`http://127.0.0.1:8000/`

API documentation is available at:

`http://127.0.0.1:8000/docs`

## Database

The application uses MySQL.

Database name:

`smart_ecommerce`

Main tables include:

- users
- Product
- Cart
- Orders
- orderitem
- payments
- notifications

The complete database backup is provided as:

`smart_ecommerce_full_dump.sql`

## Running the Project

### Start FastAPI

Open a terminal in the project directory and run:

```cmd
uvicorn fast_api_app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Django

Open another terminal and run:

```cmd
python manage.py runserver 8001
```

Then open:

`http://127.0.0.1:8001/`

## Stripe Test Payment

The project uses Stripe in test/sandbox mode.

For testing payments, use Stripe's test card:

- Card number: `4242 4242 4242 4242`
- Expiry: `12/34`
- CVC: `123`
- Postal code: `560001`

No real payment is made when using Stripe test mode.

## User Roles

### Customer

Customers can:

- Register and log in
- Browse products
- Add products to cart
- Create orders
- Make payments
- View order history
- View notifications
- Update profile

### Seller

Sellers can:

- Access the seller dashboard
- Add products
- Edit products
- Delete products
- Upload product images
- Manage available stock

### Admin

Administrators can:

- Manage users
- Manage products
- Manage orders
- View dashboard statistics
- View analytics
- Export users, products, orders and payments as CSV
- Export orders, sales and analytics as PDF

## Reports

The admin dashboard provides:

### CSV Reports

- Users CSV
- Products CSV
- Orders CSV
- Payments CSV

### PDF Reports

- Orders PDF
- Sales PDF
- Analytics PDF

## Database Backup

To create a fresh SQL dump of the current MySQL database:

```cmd
mysqldump -u root -p smart_ecommerce > smart_ecommerce_full_dump.sql
```

The command creates a backup containing the database structure and existing data.

## Project Deliverables

The project submission includes:

- Django frontend source code
- FastAPI backend source code
- MySQL database SQL dump
- Postman API collection
- Project screenshots
- Project demonstration video
- Project documentation

## Testing

The FastAPI APIs can be tested using:

`http://127.0.0.1:8000/docs`

The Django web application can be tested using:

`http://127.0.0.1:8001/`

## GitHub

The project source code is maintained using Git and GitHub.

Before final submission, make sure the latest working code, database dump and required documentation are included in the project repository.
