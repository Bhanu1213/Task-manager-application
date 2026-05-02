# Task Manager - Project Management System

A comprehensive task management system with role-based access control (Admin/Member), project tracking, and task assignment features. Built with Flask, SQLite, and modern HTML/CSS.

## 📋 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Default Login Credentials](#default-login-credentials)
- [User Roles & Permissions](#user-roles--permissions)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Screenshots](#screenshots)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## ✨ Features

### Admin Capabilities
- ✅ Create, view, and delete projects
- ✅ Add/remove team members to projects
- ✅ Create, assign, and delete tasks
- ✅ View all projects across the organization
- ✅ Update any task status
- ✅ Complete dashboard with organization-wide statistics

### Member Capabilities
- ✅ View assigned projects only
- ✅ Update status of tasks assigned to them
- ✅ Track personal tasks with deadlines
- ✅ View project progress and team members
- ✅ Personal dashboard with task statistics

### Core Features
- 🔐 User Authentication (Signup/Login)
- 👥 Role-based Access Control (RBAC)
- 📁 Project Management
- 📝 Task Management with Status Tracking
- 📊 Interactive Dashboard with Analytics
- 📅 Deadline and Priority Management
- 👤 User Profile Management
- 🎨 Responsive Modern UI
- 🔒 Secure Password Hashing
- 💾 SQLite Database (No setup required)

## 🛠 Tech Stack

### Backend
- **Flask 2.3.3** - Web framework
- **Flask-SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **Flask-Bcrypt** - Password hashing
- **SQLite** - Lightweight database (can be switched to PostgreSQL)

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with modern gradients and animations
- **Vanilla JavaScript** - Interactive modals and dynamic content
- **Responsive Design** - Mobile-friendly layout

## 📥 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step-by-Step Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/task-manager.git
cd task-manager