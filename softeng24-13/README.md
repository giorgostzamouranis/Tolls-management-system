# Toll Management System

The *Toll Management System* is a full‐stack application designed to manage toll station operations. It includes a REST API (back-end) for managing toll stations, passes, and related data; a web front-end for visualization and interaction; and a CLI client for administrative operations. The system also provides features for data analysis and reporting, such as toll traffic charts, pass analysis, daily revenue charts, and more.

---

## Table of Contents

- [Features](#features)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Creators](#Creators)



---

## Features

- *User Authentication:* Secure login and logout with session management.
- *Toll Station Management:* Create, update, and reset toll stations and passes.
- *Data Population:* Scripts to populate the database using CSV files.
- *Debt/Setoff Calculation:* Compute net balances (debts) between operators.
- *REST API:* Endpoints for login, logout, toll station passes retrieval, pass analysis, passes cost, charges by visiting operators, and healthchecks.
- *CLI Client:* A command-line interface (CLI) for performing administrative actions such as resetting passes, adding passes from a CSV file, and retrieving various reports.
- *Web Front-end:* HTML templates with CSS for a modern user interface. Features include:
  - Home page
  - Login page
  - Pages for viewing statistics: Toll Traffic charts (line chart and heatmap), daily revenue (money spent) bar chart, revenues by vehicle type bar chart, top 3 roads by passes.
  - A CLI access page for administrators.
- *OpenAPI Documentation:* A JSON file describing the API endpoints for integration and testing.
- *Automated API Testing:* A Postman collection is provided for API testing.

---

## Folder Structure

The project is organized as follows:

Note:  
- The *back-end* folder contains Python scripts implementing the API, database connections, and business logic.
- The *cli-client* folder includes the CLI client scripts (both Bash and Python).
- The *documentation* folder has the API documentation in OpenAPI (Swagger) format.
- The *front-end* folder contains HTML templates and static assets (CSS) for the web interface.
- The *tests* folder includes a Postman collection for API testing.
- CSV files and SQL scripts are located in the root directory.

---

## Installation
There is a "requirements.txt" file that contains all the libraries used in the project.
Execute "pip install -r requirements.txt" to install all the libraries.


### Prerequisites

- *Python 3.7+* (preferably 3.8 or newer)
- *MySQL Server* (ensure the credentials in your configuration match your MySQL setup)
- *pip* (Python package installer)
- *git* (optional, for cloning the repository)

## Creators  
- Katsaidonis Nikolaos  
- Katsiadramis Kyriakos  
- Tzamouranis Georgios  
- Fotakis Andreas

 



