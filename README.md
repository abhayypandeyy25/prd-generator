# PM Clarity - PRD Builder

A web application for Product Managers to gain complete clarity on their product ideas before writing a PRD. Based on 150+ questions distilled from 300+ Lenny's Podcast interviews with world-class product leaders.

## Features

- **Context Tab**: Upload emails, docs, meeting notes, voice transcripts, and other context
- **Questions Tab**: 150 questions organized by 10 sections, with AI-powered prefill from context
- **PRD Tab**: Auto-generate comprehensive PRD and export to Markdown or Word

## Tech Stack

- **Frontend**: Vue.js 3 + Vite + Pinia
- **Backend**: Python Flask
- **AI**: Claude API (Anthropic)
- **Database**: Supabase (PostgreSQL + Storage)
- **Export**: Markdown + Word (.docx)

## Prerequisites

- Node.js 18+
- Python 3.10+
- Supabase account
- Anthropic API key

## Setup Instructions

### 1. Clone and Navigate

```bash
cd pm-clarity
```

### 2. Supabase Setup

Create a new Supabase project and run the following SQL to create tables:

```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Context files table
CREATE TABLE context_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_url TEXT,
    extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Question responses table
CREATE TABLE question_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    response TEXT,
    ai_suggested BOOLEAN DEFAULT FALSE,
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, question_id)
);

-- Generated PRDs table
CREATE TABLE generated_prds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    content_md TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_context_files_project ON context_files(project_id);
CREATE INDEX idx_question_responses_project ON question_responses(project_id);
CREATE INDEX idx_generated_prds_project ON generated_prds(project_id);
```

Also create a storage bucket:
1. Go to Storage in Supabase
2. Create a new bucket called `context-files`
3. Set it to public or configure RLS policies

### 3. Environment Variables

Create `.env` file in the `backend` folder:

```bash
cd backend
cp ../.env.example .env
```

Edit `.env` with your credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
ANTHROPIC_API_KEY=your-anthropic-api-key
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

The backend will run on `http://localhost:5001`

### 5. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will run on `http://localhost:5173`

## Usage

1. **Create a Project**: Click "New Project" and give it a name
2. **Upload Context**: Drag and drop or click to upload context files (PDF, Word, Excel, TXT, Markdown, Email)
3. **Answer Questions**:
   - Click "AI Prefill from Context" to auto-fill answers based on uploaded context
   - Review and edit AI suggestions
   - Click "Confirm" for each answer you approve
4. **Generate PRD**:
   - Click "Generate PRD" to create your document
   - Export as Markdown or Word

## Project Structure

```
pm-clarity/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ContextTab.vue
│   │   │   ├── QuestionsTab.vue
│   │   │   ├── QuestionCard.vue
│   │   │   └── PRDTab.vue
│   │   ├── stores/
│   │   │   └── projectStore.js
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── context.py
│   │   │   ├── questions.py
│   │   │   ├── prd.py
│   │   │   └── projects.py
│   │   ├── services/
│   │   │   ├── claude_service.py
│   │   │   ├── supabase_service.py
│   │   │   ├── file_processor.py
│   │   │   └── prd_generator.py
│   │   ├── data/
│   │   │   └── questions.json
│   │   └── templates/
│   │       └── prd_template.md
│   ├── requirements.txt
│   └── run.py
│
├── .env.example
└── README.md
```

## API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/:id` - Get project
- `DELETE /api/projects/:id` - Delete project

### Context
- `POST /api/context/upload/:projectId` - Upload files
- `GET /api/context/:projectId` - List context files
- `DELETE /api/context/file/:fileId` - Delete file

### Questions
- `GET /api/questions` - Get all questions
- `POST /api/questions/prefill/:projectId` - AI prefill
- `GET /api/questions/:projectId/responses` - Get responses
- `PUT /api/questions/:projectId/responses` - Save responses

### PRD
- `POST /api/prd/generate/:projectId` - Generate PRD
- `GET /api/prd/:projectId` - Get PRD
- `GET /api/prd/:projectId/export/md` - Export Markdown
- `GET /api/prd/:projectId/export/docx` - Export Word

## Deployment to Railway

Railway provides easy deployment for full-stack applications. Follow these steps:

### 1. Prerequisites

- Railway account (https://railway.app)
- GitHub repository with this code

### 2. Deploy Steps

1. **Push to GitHub**: Push your code to a GitHub repository

2. **Create Railway Project**:
   - Go to https://railway.app/new
   - Click "Deploy from GitHub repo"
   - Select your pm-clarity repository

3. **Configure Environment Variables**:
   In Railway dashboard, go to your service → Variables and add:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   FLASK_ENV=production
   ```

4. **Deploy**:
   - Railway will automatically detect the Dockerfile and build
   - Wait for the deployment to complete (usually 2-3 minutes)

5. **Get Your URL**:
   - Go to Settings → Networking → Generate Domain
   - Your app will be available at `https://your-app.railway.app`

### 3. Verify Deployment

- Visit your Railway URL
- Check `/api/health` endpoint returns `{"status": "healthy"}`
- Create a test project and upload a file

### Troubleshooting

- **Build fails**: Check the build logs in Railway dashboard
- **502 errors**: Ensure all environment variables are set correctly
- **File upload fails**: Verify Supabase storage bucket `context-files` exists and is accessible

## Credits

Based on the "PM's Pre-PRD Clarity Guide" with 150+ questions distilled from 300+ Lenny's Podcast interviews featuring product leaders from companies including Facebook, Instagram, Airbnb, Stripe, Netflix, Shopify, Slack, Figma, Notion, and more.
