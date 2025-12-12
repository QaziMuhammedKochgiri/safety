# SafeChild 🛡️

**Child Safety Case Management & Digital Forensics Platform**

[![CI/CD Pipeline](https://github.com/QaziMuhammedKochgiri/safety/actions/workflows/ci.yml/badge.svg)](https://github.com/QaziMuhammedKochgiri/safety/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)

## Overview

SafeChild is a comprehensive platform designed to assist child protection professionals, legal teams, and investigators in managing child safety cases. It provides tools for digital forensics, case management, evidence documentation, and secure communication.

## Features

- 📋 **Case Management** - Create, track, and manage child safety cases
- 🔍 **Digital Forensics** - Analyze mobile device data (WhatsApp, SMS, contacts)
- 📱 **Mobile Agent** - Android app for secure device data extraction
- 📄 **Document Management** - Upload and organize case evidence
- 🔐 **Role-Based Access** - Admin, investigator, and viewer roles
- 📊 **Timeline Analysis** - Visualize case events and communications
- 🔔 **Notifications** - WhatsApp and Telegram integrations
- 🔒 **Security** - End-to-end encryption for sensitive data

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.11, FastAPI, Motor (MongoDB) |
| **Frontend** | React 18, Tailwind CSS, shadcn/ui |
| **Database** | MongoDB 7.0 |
| **Mobile** | Android (Kotlin) |
| **Messaging** | WhatsApp Web.js, Telegram Bot API |
| **Deployment** | Docker, Docker Compose, Nginx |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/QaziMuhammedKochgiri/safety.git
cd safety

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d
```

Access the application at `http://localhost:3000`

### Development Setup

<details>
<summary><b>Backend (Python)</b></summary>

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```
</details>

<details>
<summary><b>Frontend (React)</b></summary>

```bash
cd frontend
yarn install
yarn start
```
</details>

## Project Structure

```
safechild/
├── backend/                # FastAPI backend
│   ├── routers/           # API endpoints
│   ├── forensics/         # Digital forensics engine
│   ├── models.py          # Database models
│   └── server.py          # Main application
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components
│   │   └── lib/           # Utilities
├── android-agent/         # Mobile data extraction app
├── whatsapp-service/      # WhatsApp notification service
├── telegram-service/      # Telegram bot service
├── docker-compose.yml     # Container orchestration
└── docs/                  # Documentation
```

## API Documentation

Once running, access the API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security

- All sensitive data is encrypted at rest
- JWT-based authentication
- Role-based access control
- Audit logging for all actions
- See [SECURITY.md](SECURITY.md) for vulnerability reporting

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This software is intended for authorized child protection professionals and legal investigators. Users are responsible for ensuring compliance with all applicable laws and regulations regarding data privacy and digital evidence handling.

---

**SafeChild** - Protecting children through technology 🛡️
