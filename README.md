# AgriLink

AgriLink is a comprehensive platform designed to connect farmers and buyers, facilitating the sale and purchase of agricultural products. The platform provides features for user registration, product management, order processing, and role-based access control.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Features

- **User Registration and Authentication**: Separate registration and login for farmers and buyers.
- **Role-Based Access Control**: Ensures that only authorized users can access specific endpoints.
- **Product Management**: Farmers can add, update, view, and delete their products.
- **Order Management**: Buyers can create orders, and farmers can view and confirm their orders.
- **Dashboard**: Farmers can view statistics and recent orders.
- **Caching**: Utilizes Redis for caching frequently accessed data.

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/agrilink.git
    cd agrilink
    ```

2. **Create a virtual environment**:

    ```bash
    python3 -m venv env
    source env/bin/activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database**:

    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

## Configuration

1. **Environment Variables**: Create a [.env](http://_vscodecontentref_/1) file in the root directory and add the following variables:

    ```env
    SECRET_KEY=your_secret_key
    DATABASE_URI=your_database_uri
    MAIL_USERNAME=your_email@example.com
    MAIL_PASSWORD=your_email_password
    REDIS_URL=redis://localhost:6379/0
    ```

2. **Flask Configuration**: The application configuration is managed in [config.py](http://_vscodecontentref_/2).

## Usage

1. **Run the application**:

    ```bash
    flask run
    ```

2. **Access the application**: Open your browser and navigate to `http://localhost:5000`.

## API Endpoints

### Authentication

- **Register Farmer**: `POST /api/v1/signup/farmer`
- **Register Buyer**: `POST /api/v1/signup/buyer`
- **Login Farmer**: `POST /api/v1/login/farmer`
- **Login Buyer**: `POST /api/v1/login/buyer`
- **Logout**: `POST /api/v1/logout`
- **Refresh Token**: `POST /api/v1/refresh_token`
- **Change Password**: `POST /api/v1/change_password`
- **Forgot Password**: `POST /api/v1/forgot_password`
- **Reset Password**: `POST /api/v1/reset_password/<token>`

### Products

- **Add Product**: `POST /api/v1/products/add` (Farmer only)
- **View Products**: `GET /api/v1/products`
- **Update Product**: `PUT /api/v1/products/update/<int:id>` (Farmer only)
- **View Product by Category**: `GET /api/v1/products/category/<string:category>`
- **View Product by ID**: `GET /api/v1/products/<int:id>`
- **Delete Product**: `DELETE /api/v1/products/delete/<int:id>` (Farmer only)

### Orders

- **Create Order**: `POST /api/v1/orders/create` (Buyer only)
- **View Orders**: `GET /api/v1/orders` (Buyer only)
- **View Order Details**: `GET /api/v1/orders/<int:order_id>` (Buyer only)
- **View Farmer Orders**: `GET /api/v1/farmer/orders` (Farmer only)
- **Confirm Farmer Order**: `PATCH /api/v1/farmer/orders/<int:order_id>/confirm` (Farmer only)

### Dashboard

- **Get Dashboard Stats**: `GET /api/dashboard/stats` (Farmer only)
- **Get Recent Orders**: `GET /api/dashboard/recent-orders` (Farmer only)
- **Get Available Products**: `GET /api/dashboard/available-products` (Farmer only)

## Contributing

1. **Fork the repository**.
2. **Create a new branch**:

    ```bash
    git checkout -b feature/your-feature-name
    ```

3. **Make your changes**.
4. **Commit your changes**:

    ```bash
    git commit -m "Add your commit message"
    ```

5. **Push to the branch**:

    ```bash
    git push origin feature/your-feature-name
    ```

6. **Create a pull request**.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
