# AgriLink

## Description

AgriLink is a project aimed at connecting agricultural stakeholders, facilitating information exchange, and improving agricultural practices through digital solutions.

## Features

- User authentication and authorization
- Real-time data sharing
- Agricultural resource management
- Market connectivity
- Analytics and reporting

## Installation

```bash
# Clone the repository
git clone https://github.com/muga14/agrilink.git

# Navigate to project directory
cd agrilink

# Create a virtual environment
python -m venv env

# Start the virtual environment
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Start the server
flask run
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```properties
SECRET_KEY=your_secret_key
DATABASE_URI=your_database_url
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_email_app_password
```

> **Important**: Never commit your `.env` file to version control. Make sure it's listed in your `.gitignore`.

For security, always use environment variables for sensitive information like API keys and passwords.

## API Documentation

API documentation is available at `/api/docs` after starting the server.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Contact

For support or queries, please contact the development team.