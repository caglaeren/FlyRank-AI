# Secure Task Management API with FastAPI, PostgreSQL & Supabase Auth

This project is a secure Task Management and Authentication API built with FastAPI, PostgreSQL, and Supabase Auth, fully containerized with Docker Compose.

## 🚀 Quick Start (One-Command Run)

To run this project locally, ensure you have **Docker** and **Docker Compose** installed on your machine.

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd my_crud_api
   ```

2. **Set up the environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Run everything with a single command:**
   ```bash
   docker compose up --build
   ```

The API will be available at http://localhost:8000, and the PostgreSQL database will automatically initialize.

## 🛠️ Environment Variables
| Variable | Description | Example |
| :--- | :--- | :--- |
| DATABASE_URL | PostgreSQL connection string | postgres://postgres:dev@db:5432/tasks |
| SUPABASE_URL | Supabase Project URL | https://xyz.supabase.co |
| SUPABASE_KEY | Supabase Anon/Service Key| eyJhbGciOi... |



## API Endpoints

| Method | Endpoint | Description | Requires Auth? |
| :--- | :--- | :--- | :--- |
| POST | /auth/signup | Register a new user | No |
| POST | /auth/login | Login and receive JWT tokens| No |
| POST | /auth/logout | Logout user session | Yes (Bearer Token) |
| GET | /public/info | Public info endpoint | No |
| GET | /protected/profile | Get authenticated user profile| Yes (Bearer Token) |
| GET | /protected/dashboard | Get authenticated user dashboard| Yes (Bearer Token) |
| POST | /tasks | Create a new task | No |
| GET | /tasks | List all tasks| No |
| PUT | /tasks/{id} | Update an existing task | No |
| DELETE | /tasks/{id} | Delete a task | No |


## Swagger UI & Bearer Authentication
Access the interactive API documentation at: `http://localhost:8000/docs`

Protected endpoints feature interactive padlock icons. Click **Authorize**, paste your Supabase JWT `access_token`, and test secure routes directly from the browser without manual headers.

## Database Configuration (PostgreSQL & Docker)

- **Why PostgreSQL was chosen:** PostgreSQL is a powerful, enterprise-class open-source relational database system that provides robust concurrency, reliability, and seamless containerization support via Docker.

- **How data persistence works:** The database state is securely stored using a Docker volume (`taskdata`), ensuring data is preserved even when containers are stopped or recreated.

- **Automatic Database Creation:** The project is configured so that someone cloning the repository can run `docker compose up` and automatically set up the database structure without manual intervention.

## Example curl Output (GET)

```bash
curl -i http://localhost:8000/tasks
```

**JSON**
```bash
[
  {"id": 1, "title": "Complete the AI projects", "done": false},
  {"id": 2, "title": "Feed the cats", "done": true}
]
```


## API Documentation and Testing

Here are the verification screenshots for the CRUD operations performed via Swagger UI:

### 1. Create a Task (POST)
![Create Task](images/first_post.png)

### 2. Read Tasks (GET)
![List All Tasks](images/get_after_first_post.png)

![Get Single Task](images/get_only_one_id.png)

### 3. Update a Task (PUT)
![Update Task](images/put_for_id_3.png)

![Verify Update](images/get_after_first_put.png)

### 4. Delete a Task (DELETE)
![Delete Task](images/delete_id_4.png)

![Verify Deletion](images/get_all_after_id_4_delete.png)

### 5. Supabase Auth & Protected Endpoints (Swagger UI)

![Swagger UI Bearer Auth](images/swagger_ui.png)


### Database Viewer Screenshot
![Database Viewer](images/postgresql_docker1.png)



### Example SQL Query Executed
```sql
-- Update all tasks to mark them as completed
UPDATE tasks SET done = TRUE;

```

## About the Developer
**Tuğba Çağla EREN** - Backend AI Engineering Intern at FlyRank AI
- [LinkedIn Profile](https://www.linkedin.com/in/cagla-eren/)
- Passionate about Data Science, Machine Learning, and RAG architectures.