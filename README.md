# SkillentHub

SkillentHub is a comprehensive platform designed to bridge the gap between talent and opportunities. It serves as a centralized hub for recruitment, professional networking, and skill development, connecting job seekers, students, and professionals with recruiters and companies.

## 🚀 Features

SkillentHub offers a wide range of features to support its ecosystem:

### 👤 User Profiles & Portfolio
- **Detailed Profiles**: Showcase education, skills, work experience, and achievements.
- **Portfolio Management**: Upload and manage project files and documents.
- **Resume/CV**: Auto-generated or custom uploaded resumes.

### 🤝 Networking & Community
- **Connections**: Send and accept connection requests to build a professional network.
- **Network Graph**: Visualize and explore your professional connections.
- **Teams**: Create and manage teams for hackathons, competitions, or projects.
- **Team Invitations**: Invite members to join your teams.

### 💼 Opportunities
- **Job & Internship Portal**: Browse and apply for jobs and internships.
- **Events & Competitions**: Discover and register for hackathons, workshops, and competitions.
- **Application Tracking**: Track the status of your applications in real-time.

### 📢 Communication
- **Messaging System**: Real-time chat with connections and recruiters.
- **Notifications**: Stay updated with in-app notifications for applications, connection requests, and messages.
- **Email Alerts**: Important updates sent directly to your inbox.

### 🏢 Recruiter Features
- **Recruiter Dashboard**: sophisticated dashboard to manage recruitment processes.
- **Job Posting**: Create, edit, and manage job and internship listings.
- **Candidate Management**: View applicants, shortlist candidates, and schedule interviews.
- **Data Export**: Export applicant data for offline analysis.

### 🛡️ Security & Settings
- **Role-Based Authentication**: Secure login for Users and Recruiters.
- **OTP Verification**: Enhanced security for sensitive actions.
- **Password Reset**: Secure recovery options.
- **Privacy Settings**: Control who can see your profile and data.

## 🛠️ Tech Stack

- **Backend**: Python (Flask Framework)
- **Database**: MySQL
- **ORM/Database Tools**: PyMySQL
- **Authentication**: Flask-Session, Bcrypt
- **Email**: Flask-Mail
- **Environment Management**: Python-Dotenv

## 🏁 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

- **Python**: 3.8 or higher
- **MySQL**: Server installed and running

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/SkillentHub.git
    cd SkillentHub
    ```

2.  **Create and activate a virtual environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    - Copy the example environment file:
        ```bash
        # Windows
        copy .env.example .env

        # macOS/Linux
        cp .env.example .env
        ```
    - Open `.env` and configure your database credentials, secret key, and email settings.

    ```ini
    # Database Configuration (MySQL)
    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=root
    DB_PASSWORD=your_password  <-- Update this
    DB_NAME=skillenthub
    ```

5.  **Initialize the Database**
    - Ensure your MySQL server is running.
    - Create the database specified in your `.env` file (default: `skillenthub`).
    - *Note: If there are SQL scripts or migration commands, run them here. (e.g., `flask db upgrade` if using Flask-Migrate, or manually importing a .sql file)*

6.  **Run the Application**
    ```bash
    python run.py
    ```
    The application will start at `http://localhost:5000` (or the port specified in `.env`).

## 📂 Project Structure

```
SkillentHub/
├── app/
│   ├── blueprints/         # Route controllers (auth, jobs, profile, etc.)
│   ├── database/           # Database connection and helper functions
│   ├── models/             # Data models and logic
│   ├── services/           # Business logic layer
│   ├── static/             # CSS, JavaScript, Images
│   ├── templates/          # HTML Templates (Jinja2)
│   └── utils/              # Helper utilities
├── config.py               # Application configuration classes
├── run.py                  # Entry point
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (gitignored)
```

## 🤝 Contribution

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
