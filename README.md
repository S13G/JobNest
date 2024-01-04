# JobNest - A Job Finder Platform For Students

![logo.png](static%2Flogo.png)

## 🚀 JobNest: Your Dream Job is Just a Click Away 🚀

Welcome to JobNest, the ultimate job portal platform designed specifically for students. We're here to help you find the perfect job you aspire for right after graduation. With our platform, you can register, apply for jobs, view job lists, submit your CV, chat with recruiters, and much more. Let's navigate the world of opportunities together!

## JobNest API Link

https://jobnest.vercel.app/

## Table of Contents

- [Introduction](#jobnest---your-job-finder-platform)
- [Key Features](#key-features)
- [Testing](#testing)
- [Technologies Used](#technologies-used)
- [Getting Started](#getting-started)

## Key Features

1. **Registration:** Register as a job seeker or recruiter.
2. **Job Application:** Apply for jobs easily.
3. **Job Listings:** View a list of available jobs.
4. **CV Submission:** Submit your CV for potential employers.
5. **Chat with Recruiters:** Engage in meaningful conversations with recruiters.
6. **Video and Voice Calls:** Connect with recruiters through video and voice calls.
7. **Interviews:** Prepare for interviews and conduct them online.
8. **Job Creation and Management:** Recruiters can create, edit, update, and delete jobs.
9. **Job Review:** Recruiters can review applications for their jobs.

## Testing

We've thoroughly tested our platform to ensure a smooth and efficient user experience. If you face any issues, feel free to reach out

## Technologies Used

- Python
- Django, Django Rest Framework
- SQLite3, PostgreSQL
- Docker and Docker-Compose
- HTML5 & CSS
- Railway for deployment
- Neon.tech for database
- Cloudinary
- Gmail for email services

## Getting Started

Follow these steps to get the project up and running on your local machine:

1. Clone the repository:

        git clone https://github.com/S13G/JobNest.git
2. Navigate to the project directory:

        cd JobNest
3. Rename the ``.env.template`` to ``.env`` and update the values.


4. Build and run the service with

        docker-compose up --build
    or execute the command below in case permission is denied and root user/permission is needed
    
        sudo docker-compose up --build

5. Launch a new terminal session and run the following commands(if you are not using docker, but for
  caution: `run them`)

        django mm
      The command above makes the migrations if there are some unapplied migrations
    
        django m
      The command above performs the database migrations


6. Create an admin user with the command below(make sure you fill in the admin details in the env):

        django createsu
    After creating the superuser, access the admin panel and login with your admin credentials with the
  link https://localhost:8000/admin/


7. Add your data through the swagger doc and you can download the schema and import it into your postman collection 
