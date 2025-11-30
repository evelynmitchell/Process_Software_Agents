# Design Doc: Containerized User Profiles

**Date:** November 30, 2025
**Status:** Draft
**Author:** Claude (ASP Development Assistant)

## 1. Objective

To design a Docker-based architecture that creates isolated execution environments for the three primary ASP personas (Sarah, Alex, Jordan) and an Administrative role.

This enables:
1.  **Role Simulation:** accurately simulating multi-user interaction with the platform.
2.  **Environment Isolation:** Each persona has its own git configuration, credentials, and active workspace state.
3.  **Scalability:** Moving from a monolithic local execution to a micro-service-like structure where agents run "on behalf of" specific users.

## 2. Personas & Roles

| Persona | Role | Container Name | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Sarah** | Engineering Manager | `asp-sarah` | Process oversight, metric review, approval of high-level plans. |
| **Alex** | Senior Developer | `asp-alex` | Code generation, implementation, technical design, bug fixing. |
| **Jordan** | Product Manager | `asp-jordan` | Requirement definition, acceptance testing, priority setting. |
| **Admin** | System Administrator | `asp-admin` | Database migrations, system health, telemetry aggregation, cycle tracking. |

## 3. Architecture Design

### 3.1 Docker Compose Strategy

We will use `docker-compose.profiles.yml` to define the services. All services will share a base image (`asp-platform:latest`) but differ in configuration.

#### Shared Resources
*   **Volume: `asp-data`**: Mounted to `/app/data` in all containers. Stores the SQLite database (`asp_telemetry.db`) and shared artifacts.
*   **Network: `asp-net`**: Internal network for agent-to-agent communication (if using HTTP) or simply to allow shared access to external services.
*   **Volume: `asp-workspaces`**: Mounted to `/app/workspaces` (or specifically mapped).
    *   *Option A:* Shared workspaces volume (Users can see each other's work).
    *   *Option B:* Isolated volumes.
    *   *Decision:* **Shared Volume**, as collaboration on the same repo is a key use case.

### 3.2 Service Definitions

```yaml
services:
  # Base service (not run directly)
  asp-base:
    image: asp-platform:latest
    build: .
    volumes:
      - ./data:/app/data
      - ./workspaces:/app/workspaces
    env_file: .env

  asp-sarah:
    extends: asp-base
    container_name: asp-sarah
    environment:
      - ASP_USER_ID=sarah@example.com
      - ASP_ROLE=EngineeringManager
      - GIT_AUTHOR_NAME=Sarah Manager
      - GIT_AUTHOR_EMAIL=sarah@example.com

  asp-alex:
    extends: asp-base
    container_name: asp-alex
    environment:
      - ASP_USER_ID=alex@example.com
      - ASP_ROLE=SeniorDeveloper
      - GIT_AUTHOR_NAME=Alex Dev
      - GIT_AUTHOR_EMAIL=alex@example.com
      # Alex might need GPU access or specific dev tools

  asp-jordan:
    extends: asp-base
    container_name: asp-jordan
    environment:
      - ASP_USER_ID=jordan@example.com
      - ASP_ROLE=ProductManager
      - GIT_AUTHOR_NAME=Jordan PM
      - GIT_AUTHOR_EMAIL=jordan@example.com

  asp-admin:
    extends: asp-base
    container_name: asp-admin
    environment:
      - ASP_USER_ID=admin@example.com
      - ASP_ROLE=Administrator
    entrypoint: ["/app/scripts/admin_entrypoint.sh"]
    # Admin runs background jobs like cycle tracking, migrations, etc.
```

### 3.3 Container Entrypoints

*   **User Containers:**
    *   Default behavior: Start a Jupyter Lab instance or a shell?
    *   *Recommendation:* Start an interactive shell loop or a FastAPI server that exposes that user's "Agent Interface".
    *   For "Simulation" mode: The container runs a script that listens for tasks assigned to that user.

*   **Admin Container:**
    *   Runs migrations on startup (`scripts/migrate_telemetry_db.py`).
    *   Runs health checks.
    *   Serves the Telemetry Dashboard (Streamlit/Dash).

## 4. Implementation Details

### 4.1 Base Dockerfile
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --all-extras
COPY . .
# Git config setup script that uses env vars
COPY scripts/setup_git_user.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/setup_git_user.sh"]
CMD ["tail", "-f", "/dev/null"] # Keep alive by default
```

### 4.2 `setup_git_user.sh`
```bash
#!/bin/bash
if [ -n "$GIT_AUTHOR_EMAIL" ]; then
    git config --global user.email "$GIT_AUTHOR_EMAIL"
    git config --global user.name "$GIT_AUTHOR_NAME"
fi
exec "$@"
```

### 4.3 Workspace Management
The `WorkspaceManager` needs to be aware that it might be running in a container.
*   If `ASP_IN_CONTAINER=true`, it assumes `/app/workspaces` is the root for cloning.
*   Permissions: Ensure the user ID (UID) inside the container matches the host or use a standardized UID (1000) to avoid permission issues on the bind mount.

## 5. Usage Workflows

1.  **Collaborative Session:**
    ```bash
    docker compose -f docker-compose.profiles.yml up -d
    docker exec -it asp-alex /bin/bash
    # Alex does work...
    docker exec -it asp-sarah /bin/bash
    # Sarah reviews work...
    ```

2.  **Automated PROBE Simulation:**
    A script orchestrates tasks by sending commands to specific containers:
    *   "Jordan, define requirements for Task A." -> `docker exec asp-jordan python run_task.py ...`
    *   "Alex, implement Task A." -> `docker exec asp-alex python run_task.py ...`

## 6. Security Considerations

*   **API Keys:** Secrets (`OPENAI_API_KEY`) should be passed via Docker secrets or a restricted `.env` file, not hardcoded.
*   **Git Auth:** If pushing to remote, containers need SSH keys or PATs.
    *   *Solution:* Mount `~/.ssh` read-only or pass `GITHUB_TOKEN` as env var.

## 7. Next Steps

1.  Create `Dockerfile`.
2.  Create `docker-compose.profiles.yml`.
3.  Create entrypoint scripts.
4.  Update `WorkspaceManager` to handle container paths if needed.
