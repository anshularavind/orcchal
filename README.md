# Orchids SWE Intern Challenge Template

This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

## Backend

The backend uses `uv` for package management.

### Installation

To install the backend dependencies, run the following command in the backend project directory:

```bash
uv sync
```

### Adding API Keys (Backend)

You need to create an .env file in the backend folder with the following: 

```bash
HYPERBROWSER_API_KEY={YOUR_HYPERBROWSER_API_KEY}
ANTHROPIC_API_KEY={YOUR_ANTHROPIC_API_KEY}
OPENAI_API_KEY={YOUR_OPENAI_API_KEY}
```


### Running the Backend

To run the backend development server, use the following command:

```bash
uv run fastapi dev
```

## Frontend

The frontend is built with Next.js and TypeScript.

### Installation

To install the frontend dependencies, navigate to the frontend project directory and run:

```bash
npm install
```

### Running the Frontend

To start the frontend development server, run:

```bash
npm run dev
```
