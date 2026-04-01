# 📚 SmartRead - AI-Powered Smart Book Reading Platform

An advanced, Netflix-style book reading platform with intelligent features including controlled reading flow, quiz system, word meanings in multiple languages, and AI reading assistant.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📚 **PDF Library** | Upload PDFs, displayed in Netflix-style grid |
| 🔒 **Controlled Reading** | No skipping pages! Progress through content systematically |
| ❓ **Quiz System** | Quiz every 3 pages, 70%+ required to continue |
| 📖 **PDF to Text** | Extract and display text from PDFs (not just viewer) |
| 🌐 **Word Meaning** | Click any word → English, Hindi, Marathi meanings |
| 🤖 **AI Assistant** | Summarize, key points, simplify explanations |
| 📊 **Progress Tracking** | Auto-resume from last page, completion stats |
| 👤 **User Auth** | Login/Signup with individual progress |
| 🎨 **Netflix UI** | Dark theme, beautiful animations |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, Flask
- **Database:** MongoDB Atlas (FREE cloud)
- **PDF Processing:** PyMuPDF (fitz)
- **APIs (All FREE):**
  - Free Dictionary API (English meanings)
  - MyMemory Translation API (Hindi, Marathi)

---

## 📁 Project Structure

```
smartread/
├── app.py                    # Main Flask application (all routes)
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── README.md                # This file
│
├── templates/
│   ├── base.html            # Base template (navbar, footer, popup)
│   ├── home.html            # Netflix-style homepage
│   ├── 404.html             # Error page
│   │
│   ├── auth/
│   │   ├── login.html       # Login page
│   │   └── signup.html      # Signup page
│   │
│   ├── books/
│   │   ├── library.html     # User's book library
│   │   ├── detail.html      # Book detail with progress
│   │   └── read.html        # 📖 MAIN: Reading page with all features
│   │
│   └── admin/
│       ├── dashboard.html   # Admin stats
│       ├── upload.html      # Upload PDFs
│       └── quizzes.html     # Quiz management
│
└── static/
    ├── css/
    │   └── style.css        # Complete Netflix-style dark theme
    ├── js/
    │   └── main.js          # JavaScript utilities
    └── uploads/
        ├── books/           # PDF storage
        └── covers/          # Cover images
```

---

## 🗄️ MongoDB Schema Design

### Users Collection
```javascript
{
    _id: ObjectId,
    username: String (unique),
    email: String (unique),
    password: String (hashed),
    full_name: String,
    avatar: String (URL),
    is_admin: Boolean,
    created_at: Date,
    last_login: Date
}
```

### Books Collection
```javascript
{
    _id: ObjectId,
    title: String,
    author: String,
    description: String,
    category: String,
    pdf_path: String,
    cover_url: String,
    pages: [
        {
            page_number: Number,
            content: String,
            word_count: Number
        }
    ],
    total_pages: Number,
    total_words: Number,
    is_active: Boolean,
    uploaded_by: String (user_id),
    created_at: Date
}
```

### Reading Progress Collection
```javascript
{
    _id: ObjectId,
    user_id: String,
    book_id: String,
    current_page: Number,
    unlocked_pages: [Number],    // Pages user can access
    completed_pages: [Number],   // Pages user finished
    quiz_scores: {
        "page_3": 80,
        "page_6": 100
    },
    total_time_spent: Number (seconds),
    started_at: Date,
    last_read_at: Date,
    is_completed: Boolean
}
```

### Quizzes Collection
```javascript
{
    _id: ObjectId,
    book_id: String,
    after_page: Number,          // Quiz appears after this page
    questions: [
        {
            question: String,
            options: [String],
            correct_index: Number
        }
    ],
    passing_score: Number (default 70),
    created_at: Date
}
```

### Quiz Results Collection
```javascript
{
    _id: ObjectId,
    user_id: String,
    book_id: String,
    quiz_id: String,
    page: Number,
    score: Number,
    passed: Boolean,
    answers: [Number],
    submitted_at: Date
}
```

---

## 🚀 Setup Instructions

### Step 1: Install Python

Download Python 3.9+ from [python.org](https://www.python.org/downloads/)

Verify:
```bash
python --version
```

### Step 2: Extract Project

```bash
unzip smartread.zip
cd smartread
```

### Step 3: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install flask pymongo python-dotenv pymupdf requests
```

### Step 5: Setup MongoDB Atlas (FREE)

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create FREE account
3. Create FREE cluster (M0 Sandbox)
4. Click **"Connect"** → **"Connect your application"**
5. Copy connection string:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
   ```

6. **IMPORTANT:** Configure Network Access:
   - Go to **Network Access** → **Add IP Address**
   - Click **"Allow Access from Anywhere"** (0.0.0.0/0)

7. **Create Database User:**
   - Go to **Database Access** → **Add New Database User**
   - Create username and password

### Step 6: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your MongoDB URI
```

Your `.env` file:
```
SECRET_KEY=my-super-secret-key-123
MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/smartread
```

### Step 7: Run Application

```bash
python app.py
```

### Step 8: Open Browser

Go to: **http://localhost:5000** 🎉

---

## 📖 How to Use

### 1. Create Admin Account
- First user to sign up becomes **admin**
- Admin can upload books and create quizzes

### 2. Upload a Book (Admin)
1. Go to **Admin** → **Upload Book**
2. Fill in title, author, description
3. Select PDF file
4. Optionally add cover image
5. Click **Upload** → PDF text is extracted automatically

### 3. Create Quizzes (Admin)
1. After upload, you're redirected to quiz page
2. Create quiz for every 3 pages
3. Add 1-2 questions per quiz
4. Set correct answers

### 4. Reading a Book (User)
1. Click on any book to view details
2. Click **Start Reading**
3. Read page content
4. Click **Mark as Complete** when done
5. After every 3 pages → **Quiz appears**
6. Score 70%+ to unlock next pages

### 5. Word Meaning Feature
1. While reading, **click any word**
2. Popup shows:
   - English definition
   - Hindi translation
   - Marathi translation
   - Pronunciation (with audio)
   - Example sentences

### 6. AI Reading Assistant
1. On reading page, find **AI Assistant** panel
2. Click:
   - **Summarize** → Get page summary
   - **Key Points** → Important concepts
   - **Simplify** → Easy explanation

---

## 🔌 API Information

### Free Dictionary API
- **URL:** `https://api.dictionaryapi.dev/api/v2/entries/en/{word}`
- **No API key required**
- Returns: definitions, phonetics, examples, audio

### MyMemory Translation API
- **URL:** `https://api.mymemory.translated.net/get?q={text}&langpair=en|hi`
- **No API key required**
- **Languages:** Hindi (hi), Marathi (mr), and 50+ more
- **Limit:** 1000 requests/day free

---

## 🔐 Controlled Reading Flow Logic

```
Page 1 → Read → Complete → Unlock Page 2
Page 2 → Read → Complete → Unlock Page 3
Page 3 → Read → Complete → QUIZ REQUIRED
         ↓
    Quiz (70%+ to pass)
         ↓
    Pass → Unlock Pages 4, 5, 6
    Fail → Retry Quiz
```

**Key Rules:**
1. User can ONLY access unlocked pages
2. Cannot skip to unread pages
3. Quiz required every 3 pages
4. Must pass quiz (70%+) to continue
5. Progress saved in MongoDB

---

## 🎨 Customization

### Change Theme Colors
Edit `static/css/style.css`:
```css
:root {
    --bg-primary: #0a0a14;
    --primary: #6366f1;      /* Main accent color */
    --success: #10b981;      /* Success/complete */
    --warning: #f59e0b;      /* Quiz/warning */
    --error: #ef4444;        /* Error/failed */
}
```

### Change Quiz Frequency
In `app.py`, modify:
```python
# Current: Quiz every 3 pages
if page % 3 == 0:
    quiz_required = True

# Change to every 5 pages:
if page % 5 == 0:
    quiz_required = True
```

### Change Passing Score
In `app.py`:
```python
passed = score >= quiz.get('passing_score', 70)
# Change 70 to your desired percentage
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask
```

### "MongoDB Connection Error"
1. Check `.env` file has correct URI
2. Ensure IP is whitelisted in Atlas (Network Access)
3. Verify username/password

### "No text extracted from PDF"
- Some PDFs are image-based (scanned)
- PyMuPDF extracts only text-based PDFs
- For scanned PDFs, you'd need OCR (pytesseract)

### "Word meaning not loading"
- Check internet connection
- API might be rate-limited (wait a few minutes)

---

## 📱 Screenshots

### Homepage
- Netflix-style dark theme
- Continue Reading section
- Book library grid

### Reading Page
- Clean reading interface
- Word meaning popup on click
- AI assistant panel
- Quiz modal

### Admin Dashboard
- User statistics
- Book management
- Quiz creation

---

## 🚀 Deployment

### Deploy to Render (FREE)
1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. New Web Service → Connect GitHub
4. Set environment variables
5. Deploy!

### Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repository
3. Add MongoDB plugin
4. Deploy!

---

## 📄 License

MIT License - Free for personal and commercial use.

---

## 🙏 Credits

- **PyMuPDF** - PDF text extraction
- **Free Dictionary API** - Word meanings
- **MyMemory** - Translations
- **Font Awesome** - Icons
- **Google Fonts** - Typography

---

**Made with ❤️ for learners and readers**

**Happy Reading! 📚**
