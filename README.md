# Smart E-Commerce Platform

A Smart E-Commerce Platform using **FastAPI + MySQL** for the existing API/backend and **Django Templates + HTML/CSS/JavaScript** for the web frontend. React is not used.

## Frontend

The Django frontend provides role-based workspaces:

- **CUSTOMER** – product discovery, search/filter, product details, cart, order creation, Stripe payment initiation, order history, notifications and profile.
- **SELLER** – seller dashboard, product catalog, image upload, edit/delete products and stock visibility.
- **ADMIN** – business dashboard, users/roles, products and order-status management, plus access to Django Admin.

The frontend calls the existing FastAPI endpoints through a small Django presentation/proxy layer. The existing FastAPI business logic and API routes are not modified.

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the existing `.env` with your Auth0, Stripe and email settings. The project currently uses MySQL database `smart_ecommerce` on localhost.

Start FastAPI from the project parent directory:

```bash
uvicorn fast_api_app.main:app --reload
```

Start Django in a second terminal:

```bash
python manage.py runserver 8001
```

Open:

```text
http://127.0.0.1:8001/
```

FastAPI Swagger:

```text
http://127.0.0.1:8000/docs
```

## Notes

The existing Stripe API creates a PaymentIntent and returns a client secret. The current backend does not expose a Stripe publishable key to the frontend, so the payment page is prepared for the existing PaymentIntent flow but does not invent or expose secret credentials.

Product images are served from Django's existing `/media/` configuration.
