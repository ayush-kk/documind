╔══════════════════════════════════════════════════════════════════╗
║           DOCUMIND — COMPLETE SETUP & DEPLOYMENT GUIDE           ║
║                  From Zero to Live in 4 Steps                    ║
╚══════════════════════════════════════════════════════════════════╝

Last updated: 2024
Stack: FastAPI (Render.com) + React (Vercel) + Groq (free) + ChromaDB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 0 — PREREQUISITES (Install these first)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Python 3.10 or higher
    Check: python --version  (or python3 --version on macOS/Linux)
    Install: https://python.org/downloads

[ ] Node.js 18 or higher + npm
    Check: node --version && npm --version
    Install: https://nodejs.org/en/download

[ ] Git
    Check: git --version
    Install: https://git-scm.com/downloads

[ ] A GitHub account (for deploying to Render and Vercel)
    Create at: https://github.com


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — GET YOUR FREE API KEY (Groq)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DocuMind uses Groq for LLM inference — it's completely free, no
credit card required, and significantly faster than OpenAI.

STEP 1.1 — Create Groq Account
  1. Open your browser and go to: https://console.groq.com
  2. Click "Sign Up" (top right)
  3. Sign up with Google or GitHub for fastest setup
  4. Verify your email if prompted

STEP 1.2 — Generate Your API Key
  1. Once logged in, click "API Keys" in the left sidebar
  2. Click the button "+ Create API Key"
  3. Give it a name: "documind-dev"
  4. Click "Submit"
  5. COPY THE KEY IMMEDIATELY — it is only shown once!
     It looks like: gsk_abc123xyz...

  ⚠️  SAVE THIS KEY — you will need it in Part 2 and Part 4.

STEP 1.3 — Understand Free Tier Limits
  Groq free tier gives you (as of 2024):
  - LLaMA 3.1 70B: 6,000 tokens/minute
  - LLaMA 3.1 8B:  30,000 tokens/minute
  This is more than enough for development and demos.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — LOCAL DEVELOPMENT SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2.1 — Clone the repository
  Open your terminal and run:

    git clone https://github.com/yourusername/documind.git
    cd documind

STEP 2.2 — Set up the Python backend

  a) Navigate to the backend folder:
       cd backend

  b) Create a Python virtual environment:
       python -m venv venv

  c) Activate the virtual environment:
       On macOS / Linux:
         source venv/bin/activate
       On Windows (Command Prompt):
         venv\Scripts\activate.bat
       On Windows (PowerShell):
         venv\Scripts\Activate.ps1
       
       ✅ You should see "(venv)" in your terminal prompt.

  d) Install Python dependencies:
       pip install -r requirements.txt

       ⏱️  This will take 2–5 minutes on first run.
           It downloads PyTorch (CPU), sentence-transformers,
           ChromaDB, LangChain, FastAPI, etc.

  e) Create your environment file:
       cp .env.example .env

  f) Open .env in your text editor and fill in:
       GROQ_API_KEY=gsk_your_actual_key_here
       
       Everything else can stay as the defaults for local development.

  g) Start the FastAPI backend server:
       uvicorn main:app --reload --port 8000

       ✅ You should see:
          INFO:     Uvicorn running on http://0.0.0.0:8000
          INFO:     Started reloader process
          INFO:     ChromaDB ready at './chroma_db'
          INFO:     Loading embedding model 'all-MiniLM-L6-v2'...

       📖 Interactive API docs: http://localhost:8000/docs
       📖 Health check: http://localhost:8000/health

       NOTE: First startup downloads the ~22 MB embedding model.
             This is cached — subsequent starts are instant.

STEP 2.3 — Set up the React frontend

  a) Open a NEW terminal window/tab (keep backend running)

  b) Navigate to the frontend folder:
       cd documind/frontend    (or cd ../frontend if already in backend/)

  c) Install Node.js dependencies:
       npm install

       ⏱️  Takes about 30–60 seconds.

  d) Create local environment file:
       cp .env.example .env.local
       
       For local development, leave VITE_API_URL blank —
       the Vite dev proxy automatically forwards /api/* to localhost:8000.

  e) Start the React development server:
       npm run dev

       ✅ You should see:
          VITE v5.x.x  ready in 300ms
          ➜  Local:   http://localhost:5173/

  f) Open your browser at: http://localhost:5173

       🎉 DocuMind should be running! Try:
          - Drag a PDF into the upload zone
          - Wait for it to say "X chunks ingested"
          - Type a question in the chat box


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — PUSH TO GITHUB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Both Render.com and Vercel deploy from GitHub.

STEP 3.1 — Create a .gitignore file in the project root:

  Create the file documind/.gitignore with this content:
    # Python
    backend/venv/
    backend/__pycache__/
    backend/**/__pycache__/
    backend/*.pyc
    backend/.env
    backend/chroma_db/
    backend/doc_registry.json

    # Node
    frontend/node_modules/
    frontend/dist/
    frontend/.env.local

    # OS
    .DS_Store
    Thumbs.db

STEP 3.2 — Initialise Git and push:

    cd documind                  # project root
    git init
    git add .
    git commit -m "Initial commit: DocuMind RAG pipeline"
    
    # Create a new repo on GitHub (github.com → New repository)
    # Name it: documind
    # Don't add README (you already have one)
    
    git remote add origin https://github.com/YOURUSERNAME/documind.git
    git branch -M main
    git push -u origin main

  ✅ Your code is now on GitHub.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 4 — DEPLOY BACKEND TO RENDER.COM (Free)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4.1 — Create Render account
  1. Go to: https://render.com
  2. Click "Get Started for Free"
  3. Sign up with GitHub (recommended — easiest)

STEP 4.2 — Create a new Web Service
  1. In the Render dashboard, click "+ New" → "Web Service"
  2. Click "Connect account" next to GitHub if not connected
  3. Search for your "documind" repository
  4. Click "Connect"

STEP 4.3 — Configure the Web Service
  Fill in these fields:

    Name:                documind-backend
    Region:              Oregon (US West) — or closest to you
    Branch:              main
    Root Directory:      backend
    Runtime:             Python 3
    Build Command:       pip install -r requirements.txt
    Start Command:       uvicorn main:app --host 0.0.0.0 --port $PORT
    Plan:                Free

  ⚠️  IMPORTANT — The free Render tier:
      - Spins down after 15 minutes of inactivity
      - Cold start takes ~30 seconds
      - No persistent disk (ChromaDB data resets on restart)
      
      For a portfolio demo this is fine. For production, upgrade to
      Starter ($7/month) which adds a persistent disk.

STEP 4.4 — Add Environment Variables on Render
  Scroll down to "Environment Variables" and add:

    Key: GROQ_API_KEY
    Value: gsk_your_groq_key_here

    Key: GROQ_MODEL
    Value: llama-3.1-70b-versatile

    Key: EMBEDDING_MODEL
    Value: sentence-transformers/all-MiniLM-L6-v2

    Key: CHROMA_PERSIST_DIR
    Value: ./chroma_db

    Key: DOC_REGISTRY_PATH
    Value: ./doc_registry.json

    Key: ALLOWED_ORIGINS
    Value: https://your-app.vercel.app,http://localhost:5173
    (Update with your Vercel URL after Step 5)

STEP 4.5 — Deploy
  1. Click "Create Web Service"
  2. Watch the build logs — first deploy takes 3–8 minutes
     (downloads PyTorch, all Python packages)
  3. When you see "Your service is live" copy the URL:
     https://documind-backend-xxxx.onrender.com

  ✅ Test it: https://documind-backend-xxxx.onrender.com/health
     Should return: {"status":"healthy","service":"DocuMind API"}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 5 — DEPLOY FRONTEND TO VERCEL (Free)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5.1 — Create Vercel account
  1. Go to: https://vercel.com
  2. Click "Sign Up"
  3. Sign up with GitHub (recommended)

STEP 5.2 — Import project
  1. In the Vercel dashboard, click "Add New..." → "Project"
  2. Find your "documind" repository
  3. Click "Import"

STEP 5.3 — Configure the project
  In the configuration screen:

    Framework Preset:     Vite
    Root Directory:       frontend       ← IMPORTANT: set this!
    Build Command:        npm run build  (auto-detected)
    Output Directory:     dist           (auto-detected)
    Install Command:      npm install    (auto-detected)

STEP 5.4 — Add Environment Variables
  Expand "Environment Variables" and add:

    Name:  VITE_API_URL
    Value: https://documind-backend-xxxx.onrender.com
    (Use your actual Render URL from Step 4.5)

STEP 5.5 — Deploy
  1. Click "Deploy"
  2. Wait ~1 minute for build to complete
  3. Vercel gives you a URL like:
     https://documind-xxxx.vercel.app

STEP 5.6 — Update CORS on Render
  1. Go back to Render dashboard → your backend service
  2. Go to "Environment" tab
  3. Update ALLOWED_ORIGINS to include your Vercel URL:
     https://documind-xxxx.vercel.app,http://localhost:5173
  4. Click "Save Changes" — Render will auto-redeploy


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 6 — VERIFY EVERYTHING IS WORKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checklist:

  [ ] Backend health check passes:
        https://documind-backend-xxxx.onrender.com/health
        Expected: {"status":"healthy","service":"DocuMind API"}

  [ ] API docs load:
        https://documind-backend-xxxx.onrender.com/docs

  [ ] Frontend loads:
        https://documind-xxxx.vercel.app

  [ ] Upload test:
        - Go to your Vercel URL
        - Drag a small PDF into the upload zone
        - Should show "X chunks ingested" in green

  [ ] Chat test:
        - After upload, type: "Summarize this document"
        - Should get a grounded answer with source chunks shown


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 7 — QUICK REFERENCE: COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOCAL DEVELOPMENT:

  # Start backend (from backend/ with venv active):
  uvicorn main:app --reload --port 8000

  # Start frontend (from frontend/):
  npm run dev

  # Rebuild frontend for production (from frontend/):
  npm run build

  # Run backend tests (if you add them):
  pytest

  # Deactivate Python virtualenv:
  deactivate


GIT WORKFLOW (after making changes):

  git add .
  git commit -m "feat: your change description"
  git push origin main
  # Both Render and Vercel auto-deploy on push to main ✅


RESET LOCAL DATA (wipe ChromaDB + registry):

  cd backend
  rm -rf chroma_db/ doc_registry.json
  # Then restart the backend


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 8 — TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ISSUE: "GROQ_API_KEY is not set"
FIX:   Check your backend/.env file. Make sure the key starts with gsk_
       Make sure you're running uvicorn from the backend/ folder.

ISSUE: "pip install fails on torch"
FIX:   Try: pip install torch --index-url https://download.pytorch.org/whl/cpu
       Then: pip install -r requirements.txt

ISSUE: "PDF appears to contain no extractable text"
FIX:   The PDF is likely scanned (image-based). You'd need OCR (pytesseract).
       Try a different PDF with actual selectable text.

ISSUE: Frontend shows "Network Error" or can't reach API
FIX (local): Make sure backend is running on port 8000 and the Vite
              dev server is running on port 5173.
FIX (prod):  Check that VITE_API_URL in Vercel matches your Render URL exactly,
              and that ALLOWED_ORIGINS in Render includes your Vercel URL.

ISSUE: Render service is sleeping / first request is slow
FIX:   Free Render services sleep after 15 min inactivity. The first request
       after sleep takes ~30 seconds (cold start). This is normal.
       Consider using UptimeRobot (free) to ping /health every 14 minutes.
       Sign up at: https://uptimerobot.com

ISSUE: "chromadb.errors.InvalidCollectionException"
FIX:   ChromaDB's schema may have changed. Delete and recreate the DB:
       rm -rf backend/chroma_db backend/doc_registry.json
       Restart the backend.

ISSUE: Out of memory on Render free tier
FIX:   The free tier has 512 MB RAM. The embedding model uses ~200 MB.
       If you hit limits, switch to a smaller embedding model:
       EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  (already smallest good one)
       Or upgrade to Render Starter ($7/month) for 1 GB RAM.

ISSUE: Vercel build fails
FIX:   Make sure Root Directory is set to "frontend" in Vercel project settings.
       Check that package.json exists at frontend/package.json.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 9 — FREE SERVICES SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Service        Use                    Free Tier Limits
──────────────────────────────────────────────────────────────────
Groq           LLM inference          6K tokens/min (LLaMA 3.1 70B)
               (LLaMA 3.1 70B)        No credit card required
               
HuggingFace    Embeddings             Runs locally — completely free
               (all-MiniLM-L6-v2)    No API calls needed
               
ChromaDB       Vector database        Runs embedded — completely free
               (embedded mode)        No server needed
               
Render.com     Backend hosting        1 free web service
               (FastAPI)              Sleeps after 15 min inactivity
                                      512 MB RAM, shared CPU
                                      
Vercel         Frontend hosting       Unlimited personal projects
               (React)                Global CDN, auto HTTPS
                                      100 GB bandwidth/month
                                      
GitHub         Source control         Free for public/private repos
               + CI/CD trigger        Unlimited repositories

TOTAL COST: $0.00 / month 🎉


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 10 — NEXT STEPS & IMPROVEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Once your portfolio project is running, consider adding:

  🔐 Authentication
     - Add JWT auth with FastAPI's oauth2_password_bearer
     - Each user gets their own document namespace in ChromaDB

  🗄️  Persistent Database
     - Replace doc_registry.json with SQLite (aiosqlite) or PostgreSQL
     - Use Supabase (free PostgreSQL) for managed DB

  📊  Better Observability
     - Add LangSmith tracing (free tier) for RAG pipeline monitoring
     - Log token usage per query

  🔍  Hybrid Search
     - Combine vector search with BM25 keyword search
     - Use Reciprocal Rank Fusion (RRF) to merge results
     - Significantly improves retrieval quality

  📄  Better PDF Support
     - Add OCR for scanned PDFs using pytesseract + pdf2image
     - Extract tables using camelot or tabula-py

  🚀  Performance
     - Add Redis caching for repeated queries
     - Use async ChromaDB operations
     - Pre-warm the embedding model on startup

  💬  Streaming Responses
     - Use FastAPI StreamingResponse + Groq's stream=True
     - Frontend uses EventSource for real-time token display

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                         Good luck! 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
