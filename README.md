<div align="center">
  <img src="https://img.shields.io/badge/HOSTELLO-Automated Smart Hostel Management System using Django-092E20?style=for-the-badge&logo=django" alt="Hostello Logo">
  
  <h3>HOSTELLO</h3>
  <p>Automated Smart Hostel Management System using Django</p>

  <p>
    <a href="https://hashmil.pythonanywhere.com/" target="_blank">
      <img src="https://img.shields.io/badge/🔴_Live_Demo-hashmil.pythonanywhere.com-success?style=for-the-badge" alt="Live Demo">
    </a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white" alt="Django">
    <img src="https://img.shields.io/badge/SQLite-07405E?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white" alt="HTML5">
    <img src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white" alt="CSS3">
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript">
    <img src="https://img.shields.io/badge/Bootstrap-563D7C?style=flat-square&logo=bootstrap&logoColor=white" alt="Bootstrap">
  </p>
</div>

> **HOSTELLO** is a comprehensive, automated smart hostel management system designed to streamline and digitize daily hostel operations. By minimizing manual paperwork and maximizing efficiency, it provides a seamless experience for administrators and students alike—handling attendance, absence alerts, room allocation, and fee management in one secure platform.

---

### 🎥 Project Working Demo

https://github.com/user-attachments/assets/0fed39ea-e51d-4bab-a69c-a4a53ace6a20

<div align="center">
  <em>▶ HOSTELLO - Complete Project Walkthrough (Click Play to watch)</em>
</div>

---

## 📋 Table of Contents
- [🌟 Project Overview](#-project-overview)
- [✨ Key Features](#-key-features)
- [🏗️ System Architecture](#️-system-architecture)
- [💻 Tech Stack](#-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🗄️ Database Schema](#️-database-schema)
- [📸 Application Screens](#-application-screens)
- [🚀 Running the Application](#-running-the-application)
- [🔒 Security](#-security)
- [📜 License](#-license)

---

## 🌟 Project Overview
HOSTELLO tackles the chaotic administration of student accommodations by moving all critical operations—from daily room/mess attendance to grievance reporting—onto a centralized digital platform. The inclusion of automated guardian notifications ensures safety and accountability are maintained seamlessly.

---

## ✨ Key Features
### 👨‍💼 Admin Features
- **Dashboard Analytics:** Visual overview of total students, available rooms, fee collections, and recent activities.
- **Room Assignment & Management:** Efficient allocation and tracking of hostel rooms. Admins can create rooms, set capacities, and assign students based on preferences.
- **Smart Attendance System:** Daily tracking of student presence in rooms and the mess. 
- **Automated Guardian Alerts:** Automatically sends email alerts to parents/guardians when a student is absent beyond warning or critical thresholds.
- **Fee Management:** Transparent tracking of hostel and mess fees. Admins can generate fee invoices and track payment statuses.
- **Notices Broadcasting:** Create and publish digital announcements that instantly reflect on the student dashboard.
- **Request Management:** Handle student complaints, maintenance requests, and leave applications efficiently.
- **Premium Admin Interface:** Integrated with Jazzmin for a beautiful, responsive, and highly customizable administration panel.

### 🎓 Student Features
- **Student Dashboard:** Personalized portal displaying room details, attendance records, and pending dues.
- **Notice Board:** Real-time access to important announcements and hostel notices.
- **Fee Portal:** View detailed fee breakdowns and track payment history securely.
- **Requests & Complaints:** Submit and track the status of maintenance requests, leave applications, or general complaints directly from the portal.

---

## 🏗️ System Architecture

```text
    +-------------------+           HTTP/JSON            +-----------------------+
    |                   |  <==========================>  |                       |
    |  Frontend Web UI  |                                |   Django Web Server   |
    |  (HTML/CSS/JS)    |  <-------------------------->  |   (Views/URLs/APIs)   |
    |                   |           Templates            |                       |
    +-------------------+                                +-----------+-----------+
                                                                     |
                                                                     | ORM
                                                                     v
    +-------------------+                                +-----------+-----------+
    |                   |                                |                       |
    |   External APIs   |  <==========================>  |     Django Models     |
    | (Stripe, SMTP)    |      Payments & Emails         |    (Business Logic)   |
    |                   |                                |                       |
    +-------------------+                                +-----------+-----------+
                                                                     |
                                                                     | SQL
                                                                     v
                                                         +-----------+-----------+
                                                         |                       |
                                                         |    SQLite Database    |
                                                         |     (Data Storage)    |
                                                         |                       |
                                                         +-----------------------+
```

---

## 💻 Tech Stack

### 🎨 Frontend
| Technology | Badge | Description |
| :--- | :--- | :--- |
| **HTML5** | ![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=flat-square&logo=html5&logoColor=white) | Semantic structure for all dashboard views. |
| **CSS3** | ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=flat-square&logo=css3&logoColor=white) | Premium styling and responsive layout designs. |
| **JavaScript** | ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=flat-square&logo=javascript&logoColor=%23F7DF1E) | Interactive DOM elements and asynchronous logic. |
| **Bootstrap**| ![Bootstrap](https://img.shields.io/badge/bootstrap-%238511FA.svg?style=flat-square&logo=bootstrap&logoColor=white) | Clean and consistent UI component framework. |

### ⚙️ Backend
| Technology | Badge | Description |
| :--- | :--- | :--- |
| **Python** | ![Python](https://img.shields.io/badge/python-3670A0?style=flat-square&logo=python&logoColor=ffdd54) | Core programming language (3.10+). |
| **Django** | ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=flat-square&logo=django&logoColor=white) | High-level web framework for rapid development. |
| **Django REST** | ![DjangoREST](https://img.shields.io/badge/DJANGO--REST-ff1709?style=flat-square&logo=django&logoColor=white&color=ff1709&labelColor=gray) | Toolkit for building Web APIs. |

### 🗄️ Database, Tools & Deployment
| Technology | Badge | Description |
| :--- | :--- | :--- |
| **SQLite** | ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=flat-square&logo=sqlite&logoColor=white) | Lightweight, robust local data storage. |
| **Jazzmin** | ![Jazzmin](https://img.shields.io/badge/django--jazzmin-Premium_UI-2ea44f?style=flat-square) | Premium customized admin panel interface. |
| **PythonAnywhere** | ![PythonAnywhere](https://img.shields.io/badge/PythonAnywhere-1D9FD7?style=flat-square&logo=pythonanywhere&logoColor=white) | Live cloud server hosting & deployment. |
| **Git & GitHub**| ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=flat-square&logo=github&logoColor=white) | Version control and remote source code management. |

---

## 📁 Project Structure

```text
HOSTELLO/
├── hostello_backend/
│   ├── accounts/             # Custom user models & auth logic
│   ├── attendance/           # Room and Mess attendance tracking
│   ├── fees/                 # Payments and fee management
│   ├── hostello_backend/     # Main project settings & routing
│   │   ├── settings.py
│   │   └── urls.py
│   ├── notices/              # Notice board broadcasting
│   ├── media/              
│   ├── requests/             # Student complaints/leave ticketing
│   ├── students/             # Student profiles & room allocation
│   ├── static/               # CSS, JS, and Images
│   ├── templates/            # HTML Django templates
│   ├── manage.py
│   └── requirements.txt
├── .env                      # Environment variables (git-ignored)
├── .gitignore
├── README.md
├── run_backend.bat           # Startup script
└── run_frontend.bat          # Startup script
```

---

## 🗄️ Database Schema

| Model Name | Purpose | Key Relationships |
| :--- | :--- | :--- |
| **User** | Custom authentication model (Admin/Warden). | Base model. |
| **Student** | Stores student details, guardian info, room info. | O2O with User, FK to Room. |
| **RoomAttendance** | Daily presence/absence tracking in rooms. | FK to Student. |
| **MessAttendance** | Daily presence/absence tracking in the mess. | FK to Student. |
| **Fee** | Logs fee types, amounts, and payment status. | FK to Student. |
| **StudentRequest** | Stores complaints, leave apps, and status. | FK to Student. |
| **Notice** | Global announcements for the dashboard. | Broadcast model. |

---

## 📸 Application Screens

### 🌐 Public Portal & Essential Info
<div align="center">
  <img src="assets/01_landing_page.png" alt="Landing Page" width="850"/>
  <br><em>Modern & Responsive Landing Page</em><br><br>

  <table style="width:100%">
    <tr>
      <td align="center"><img src="assets/02_about_hostels.png" alt="About Hostels" width="400"/><br><b>Hostel Blocks & Capacity</b></td>
      <td align="center"><img src="assets/03_room_types.png" alt="Room Types" width="400"/><br><b>3D Room Previews</b></td>
    </tr>
    <tr>
      <td align="center"><img src="assets/04_facilities.png" alt="Facilities" width="400"/><br><b>Student Living Benefits</b></td>
      <td align="center"><img src="assets/05_food_menu.png" alt="Food Menu" width="400"/><br><b>Weekly Mess Menu</b></td>
    </tr>
    <tr>
      <td align="center" colspan="2"><img src="assets/06_amenities_footer.png" alt="Amenities" width="800"/><br><b>Hostel Amenities & Contact Info</b></td>
    </tr>
  </table>
</div>


### 🔐 Authentication & Onboarding
<div align="center">
  <table style="width:100%">
    <tr>
      <td align="center"><img src="assets/07_registration.png" alt="Registration" width="400"/><br><b>Secure Registration</b></td>
      <td align="center"><img src="assets/08_login.png" alt="Login" width="400"/><br><b>Student Login</b></td>
    </tr>
  </table>
</div>


### 🎓 Student Dashboard & Attendance
<div align="center">
  <table style="width:100%">
    <tr>
      <td align="center"><img src="assets/09_student_dashboard.png" alt="Student Dashboard" width="400"/><br><b>Comprehensive Student Profile</b></td>
      <td align="center"><img src="assets/10_attendance_records.png" alt="Attendance Records" width="400"/><br><b>Real-time Attendance Tracking</b></td>
    </tr>
  </table>
</div>


### 💳 Fee Management & Payments
<div align="center">
  <table style="width:100%">
    <tr>
      <td align="center"><img src="assets/13_fee_management.png" alt="Fee Management" width="400"/><br><b>Dynamic Fee Calculation</b></td>
      <td align="center"><img src="assets/15_payment_success.png" alt="Payment Success" width="400"/><br><b>Automated Receipts</b></td>
    </tr>
  </table>
</div>


### 📝 Requests, Notices & Info
<div align="center">
  <table style="width:100%">
    <tr>
      <td align="center"><img src="assets/11_my_requests_list.png" alt="Requests List" width="400"/><br><b>Leave & Complaint Status</b></td>
      <td align="center"><img src="assets/12_leave_request_form.png" alt="Request Form" width="400"/><br><b>Submission Modal</b></td>
    </tr>
    <tr>
      <td align="center"><img src="assets/16_notifications_notices.png" alt="Notifications" width="400"/><br><b>Warden Notices</b></td>
      <td align="center"><img src="assets/17_hostel_info_contact.png" alt="Hostel Info" width="400"/><br><b>Policies & Contacts</b></td>
    </tr>
  </table>
</div>

---

### 🛡️ Admin & Warden Control Panel
<div align="center">
  <table style="width:100%">
    <tr>
      <td align="center"><img src="assets/1.admin_login_page.png" alt="Admin Login" width="400"/><br><b>Secure Warden Portal Login</b></td>
      <td align="center"><img src="assets/2.admin_dashboard_overview.png" alt="Admin Dashboard" width="400"/><br><b>Centralized Admin Dashboard</b></td>
    </tr>
    <tr>
      <td align="center"><img src="assets/3.warden_profiles_list.png" alt="Warden Profiles" width="400"/><br><b>Managing Hostel Wardens</b></td>
      <td align="center"><img src="assets/4.room_management_system.png" alt="Room Management" width="400"/><br><b>Managing Room Availability & Types</b></td>
    </tr>
    <tr>
      <td align="center"><img src="assets/5.student_directory_admin.png" alt="Student Directory" width="400"/><br><b>Warden's View of Student Records</b></td>
      <td align="center"><img src="assets/6.attendance_management_enhanced.png" alt="Attendance Management" width="400"/><br><b>Bulk Attendance & Detailed Statistics</b></td>
    </tr>
    <tr>
      <td align="center"><img src="assets/7.student_request_management.png" alt="Request Management" width="400"/><br><b>Processing Leave & Complaint Requests</b></td>
      <td align="center"><img src="assets/8.automated_fee_calculation.png" alt="Fee Calculation" width="400"/><br><b>Dynamic Fee Engine: Hostel + Mess</b></td>
    </tr>
    <tr>
      <td align="center" colspan="2"><img src="assets/9.notice_board_management.png" alt="Notice Management" width="800"/><br><b>Broadcasting Warden Notices to Students</b></td>
    </tr>
  </table>
</div>

---

## 🚀 Running the Application

### 1. Clone the Repository
```bash
git clone https://github.com/Hashmil-Muhammed/HOSTELLO_Automated_Smart_Hostel_Management_System_using_Django.git
cd HOSTELLO_Automated_Smart_Hostel_Management_System_using_Django
```

### 2. Set Up Virtual Environment
```bash
python -m venv hostello_env
# Windows:
hostello_env\Scripts\activate
# macOS/Linux:
source hostello_env/bin/activate
```

### 3. Install Dependencies
```bash
cd hostello_backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the `hostello_backend/hostello_backend/` directory:
```env
SECRET_KEY=your-secure-django-secret-key-here
DEBUG=True

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe API Keys (Optional)
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

### 5. Run Migrations & Create Superuser
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Start the Server
```bash
python manage.py runserver
```
*Access the frontend at `http://127.0.0.1:8000/` and the admin panel at `http://127.0.0.1:8000/admin/`*

---

## 🔒 Security
- All sensitive credentials (such as Secret Keys and Email Passwords) are stored securely using environment variables (`.env`).
- Cross-Origin Resource Sharing (CORS) is strictly configured.
- Protected by Django's native CSRF & XSS prevention layers.
- Password hashing and secure authentication practices are enforced natively by Django.

---

## 📜 License
This project is licensed under the MIT License.

<div align="center">
  <br>
  <p>Built with 💻 and ☕ for seamless hostel management.</p>
</div>
