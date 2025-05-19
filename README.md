# 300M Time Trials Application

A web-based application for recording, ranking, and publishing 300 meter time trial times, following the coaching philosophy of Tony Hollar (RRP - Record, Rank, Publish).

## Features

- User Authentication for Coaches
- Time Trial Recording
- Comprehensive Rankings
- Data Visualization
- Notification System
- Data Management

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd 300m-trials
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost/300m_trials
```

5. Initialize the database:
```bash
psql -U postgres
CREATE DATABASE 300m_trials;
\q
```

6. Run database migrations:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Access the application at `http://localhost:5000`

## Usage

### For Coaches

1. Register a new account using the registration form
2. Log in with your credentials
3. Use the dashboard to:
   - Record new time trials
   - View recent activities
   - Access rankings and statistics

### For Viewers

1. Access the public pages:
   - Rankings (filterable by grade and time frame)
   - Most Improved Athletes
   - Statistics and trends

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Tony Hollar for the RRP coaching philosophy
- Flask and SQLAlchemy communities
- Bootstrap and Chart.js for the frontend components 