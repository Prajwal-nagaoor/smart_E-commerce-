# Smart E-Commerce Platform

A full-stack Smart E-Commerce Platform built using **Django, FastAPI, MySQL, SQLAlchemy, and Stripe**.

The platform allows customers to browse products, manage their cart, place orders, and make online payments. Sellers can manage products, while administrators can manage users, products, orders, analytics, and reports.

---

## Features

### Customer

- User registration and login
- JWT-based authentication
- Browse products
- Product categories
- Product details
- Add products to cart
- Remove products from cart
- Create orders
- Stripe payment processing
- View order history
- Track order status
- Notifications
- Update profile

### Seller

- Seller dashboard
- Add products
- Edit products
- Delete products
- Upload product images
- Manage product stock
- View seller-related information

### Admin

- Admin dashboard
- User management
- Product management
- Order management
- Order status management
- Sales analytics
- Payment statistics
- Category statistics
- Recent orders
- CSV reports
- PDF reports

---

## Technologies Used

### Backend

- Python
- FastAPI
- Django
- SQLAlchemy
- MySQL
- JWT Authentication

### Frontend

- Django Templates
- HTML
- CSS
- JavaScript
- Bootstrap
- Chart.js

### Payment

- Stripe Test Mode

### Tools

- Visual Studio Code
- Postman
- Git
- GitHub

---

## Project Architecture

The project uses two main applications.

### Django Frontend

Django is responsible for the web interface and admin-side functionality.

Django runs on:

```text
http://127.0.0.1:8001/