# XLO API SERVER


## Description
This project leverages Django REST Framework to provide a backend solution.

## Prerequisites
- Python 3.9+
- PostgreSQL
- Redis
- Ubuntu Server

## Setup Instructions

### Step 1: Prepare Ubuntu Server
Before setting up the Django application, update your system and install PostgreSQL and Redis:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server python3-pip python3-dev libpq-dev
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

### Step 2: Ensure Required Services are Active
Ensure the PostgreSQL and Redis services are running. Configure PostgreSQL with a database for the project and update your **'secret.json'** with the correct database credentials and any other necessary settings. Verify that Redis is operational as it will be required for caching and queue management.

### Step 3: Set Up the Virtual Environment
Create and activate a virtual environment for your project:
```bash
python3 -m venv /home/ubuntu/projects/myenv
source /home/ubuntu/projects/myenv/bin/activate
```

### Step 4: Install Dependencies
Install the required Python packages from **'requirements.txt'**:
```bash
pip install -r requirements.txt
```

### Step 5: Execute django setup commands
```bash
python manage.py migrate
python manage.py collectstatic # Server deployment
python manage.py createsuperuser
```

### Step 6: Start Celery Worker and Beat
```bash
celery -A your_project_name worker --loglevel=info &
celery -A your_project_name beat --loglevel=info &
```

### Step 7: Run the Development Server
```bash
python manage.py runserver
```
