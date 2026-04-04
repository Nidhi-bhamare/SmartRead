"""
📚 SmartRead - Advanced AI-Powered Book Reading Platform
=========================================================
Features:
- PDF Library with Netflix-style UI
- Smart Progress Tracking (Auto-resume)
- Controlled Reading Flow (No skipping!)
- Quiz System (Every 3 pages) - AUTO-GENERATED FROM CONTENT
- Word Meaning (English/Hindi/Marathi)
- AI Reading Assistant
- 🔥 DAILY STREAK TRACKING

Author: SmartRead Team
"""

import os
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import fitz  # PyMuPDF for PDF processing
import requests
import json
import re

# Load environment variables
load_dotenv()

# ============================================
# APP CONFIGURATION
# ============================================

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'smartread-secret-key-2024')
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

ALLOWED_EXTENSIONS = {'pdf'}

# MongoDB Connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/smartread')
try:
    client = MongoClient(MONGODB_URI)
    client.server_info()
    db = client['smartread']
    print("✅ MongoDB Connected!")
except Exception as e:
    print(f"⚠️ MongoDB Error: {e}")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['smartread']

# Collections
users_col = db['users']
books_col = db['books']
progress_col = db['reading_progress']
quizzes_col = db['quizzes']
quiz_results_col = db['quiz_results']
streaks_col = db['streaks']

# Create indexes
users_col.create_index('email', unique=True)
users_col.create_index('username', unique=True)
progress_col.create_index([('user_id', 1), ('book_id', 1)])
streaks_col.create_index('user_id', unique=True)


# ============================================
# HELPER FUNCTIONS
# ============================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        # Check if user actually exists
        user = get_current_user()
        if not user:
            session.clear()
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = users_col.find_one({'_id': ObjectId(session['user_id'])})
        if not user or not user.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' in session:
        try:
            user = users_col.find_one({'_id': ObjectId(session['user_id'])})
            if user:
                # Safely get streak info
                try:
                    user['streak'] = get_user_streak(str(user['_id']))
                except:
                    user['streak'] = {'current_streak': 0, 'longest_streak': 0, 'total_reading_days': 0}
                return user
        except Exception as e:
            print(f"Error getting user: {e}")
            session.clear()
    return None


# ============================================
# 🔥 STREAK TRACKING
# ============================================

def get_user_streak(user_id):
    try:
        streak = streaks_col.find_one({'user_id': str(user_id)})
        if not streak:
            streak = {
                'user_id': str(user_id),
                'current_streak': 0,
                'longest_streak': 0,
                'last_read_date': None,
                'total_reading_days': 0
            }
            try:
                streaks_col.insert_one(streak)
            except:
                pass  # Ignore if already exists
        return streak
    except Exception as e:
        print(f"Streak error: {e}")
        return {'current_streak': 0, 'longest_streak': 0, 'total_reading_days': 0}

def update_streak(user_id):
    today = datetime.utcnow().date()
    streak = get_user_streak(user_id)
    
    last_read = streak.get('last_read_date')
    if last_read:
        if isinstance(last_read, datetime):
            last_read = last_read.date()
    
    current_streak = streak.get('current_streak', 0)
    longest_streak = streak.get('longest_streak', 0)
    total_days = streak.get('total_reading_days', 0)
    
    if last_read == today:
        return streak
    elif last_read == today - timedelta(days=1):
        current_streak += 1
        total_days += 1
    else:
        current_streak = 1
        total_days += 1
    
    if current_streak > longest_streak:
        longest_streak = current_streak
    
    streaks_col.update_one(
        {'user_id': str(user_id)},
        {'$set': {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_read_date': datetime.utcnow(),
            'total_reading_days': total_days
        }},
        upsert=True
    )
    
    return {'current_streak': current_streak, 'longest_streak': longest_streak}


# ============================================
# 🤖 AUTO-GENERATE QUIZ FROM CONTENT
# ============================================

def generate_quiz_from_content(pages_content):
    """Auto-generate quiz from page content"""
    try:
        questions = []
        
        # Safely get content
        if not pages_content:
            return get_fallback_questions()
        
        full_text = ' '.join([p.get('content', '') if isinstance(p, dict) else str(p) for p in pages_content])
        
        if not full_text or len(full_text) < 50:
            return get_fallback_questions()
        
        sentences = re.split(r'[.!?]', full_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and len(s.split()) > 5]
        
        if not sentences:
            return get_fallback_questions()
        
        random.shuffle(sentences)
        
        # Fill-in-the-blank questions
        for sentence in sentences[:4]:
            words = sentence.split()
            if len(words) >= 6:
                important_words = [w for w in words if len(w) > 4 and w.isalpha() and w.lower() not in 
                                 ['which', 'there', 'their', 'would', 'could', 'should', 'about', 'these']]
                if important_words:
                    blank_word = random.choice(important_words)
                    question_text = sentence.replace(blank_word, "_____", 1)
                    wrong_options = generate_wrong_options(blank_word, full_text)
                    options = [blank_word] + wrong_options[:3]
                    # Ensure we have 4 options
                    while len(options) < 4:
                        options.append(f"Option {len(options)}")
                    random.shuffle(options)
                    questions.append({
                        'question': f"Fill in the blank:\n\"{question_text[:200]}\"",
                        'options': options[:4],
                        'correct_index': options.index(blank_word)
                    })
                    if len(questions) >= 2:
                        break
        
        # True/False question
        if sentences:
            questions.append({
                'question': f"Is this statement from the reading correct?\n\"{sentences[0][:150]}...\"",
                'options': ['Yes, this is correct', 'No, this is incorrect', 'Partially correct', 'Cannot determine'],
                'correct_index': 0
            })
        
        # Comprehension question
        words = full_text.split()
        word_freq = {}
        for word in words:
            word = re.sub(r'[^a-zA-Z]', '', word).lower()
            if len(word) > 5:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        if sorted_words:
            topic = sorted_words[0][0]
            questions.append({
                'question': "What is the main concept discussed in these pages?",
                'options': [f"Topics related to {topic}", "Historical events", "Scientific research", "Personal stories"],
                'correct_index': 0
            })
        
        # Ensure we have at least 3 questions
        while len(questions) < 3:
            questions.extend(get_fallback_questions())
        
        return questions[:3]
    
    except Exception as e:
        print(f"Quiz generation error: {e}")
        return get_fallback_questions()

def generate_wrong_options(correct_word, text):
    words = re.findall(r'\b[A-Za-z]{4,}\b', text)
    words = list(set([w.lower() for w in words if w.lower() != correct_word.lower()]))
    common = ['however', 'therefore', 'although', 'because', 'important', 'different']
    words.extend(common)
    random.shuffle(words)
    return words[:3]

def get_fallback_questions():
    return [
        {'question': "What was the main theme of the pages you read?", 
         'options': ['Knowledge and learning', 'Adventure', 'Science', 'History'], 'correct_index': 0},
        {'question': "Did you understand the key concepts?",
         'options': ['Yes, completely', 'Mostly', 'Partially', 'Need to re-read'], 'correct_index': 0},
        {'question': "Rate the content difficulty:",
         'options': ['Easy', 'Moderate', 'Challenging', 'Very difficult'], 'correct_index': 1}
    ]


def extract_pdf_pages(pdf_path):
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("blocks")
            page_text = ""
            for b in blocks:
                if len(b) >= 7 and b[6] == 0:
                    block_text = re.sub(r'\s+', ' ', b[4]).strip()
                    if block_text:
                        page_text += block_text + "\n\n"
            text = page_text.strip() or re.sub(r'\s+', ' ', page.get_text("text")).strip()
            pages.append({'page_number': page_num + 1, 'content': text, 'word_count': len(text.split())})
        doc.close()
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return pages


def get_reading_progress(user_id, book_id):
    progress = progress_col.find_one({'user_id': str(user_id), 'book_id': str(book_id)})
    if not progress:
        progress = {
            'user_id': str(user_id), 'book_id': str(book_id), 'current_page': 1,
            'unlocked_pages': [1], 'completed_pages': [], 'quiz_scores': {},
            'total_time_spent': 0, 'started_at': datetime.utcnow(),
            'last_read_at': datetime.utcnow(), 'is_completed': False
        }
        progress_col.insert_one(progress)
    return progress


def update_progress(user_id, book_id, page_number, time_spent=0):
    progress = get_reading_progress(user_id, book_id)
    completed = list(set(progress.get('completed_pages', []) + [page_number]))
    unlocked = list(set(progress.get('unlocked_pages', [1])))
    
    if page_number not in completed:
        completed.append(page_number)
    
    next_page = page_number + 1
    if next_page not in unlocked and page_number % 3 != 0:
        unlocked.append(next_page)
    
    progress_col.update_one(
        {'user_id': str(user_id), 'book_id': str(book_id)},
        {'$set': {'current_page': page_number, 'completed_pages': completed,
                  'unlocked_pages': unlocked, 'last_read_at': datetime.utcnow()},
         '$inc': {'total_time_spent': time_spent}}
    )
    update_streak(user_id)
    return {'completed': completed, 'unlocked': unlocked}


# ============================================
# AUTH ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if session user actually exists
    if 'user_id' in session:
        user = get_current_user()
        if user:
            return redirect(url_for('home'))
        else:
            # User doesn't exist - clear invalid session
            session.clear()
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        try:
            user = users_col.find_one({'email': email})
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                
                try:
                    users_col.update_one({'_id': user['_id']}, {'$set': {'last_login': datetime.utcnow()}})
                except:
                    pass
                
                flash(f'Welcome back, {user["username"]}!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('auth/login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if session user actually exists
    if 'user_id' in session:
        user = get_current_user()
        if user:
            return redirect(url_for('home'))
        else:
            session.clear()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        
        errors = []
        if len(username) < 3: errors.append('Username must be at least 3 characters')
        if '@' not in email: errors.append('Invalid email')
        if len(password) < 6: errors.append('Password must be at least 6 characters')
        if users_col.find_one({'email': email}): errors.append('Email already registered')
        if users_col.find_one({'username': username.lower()}): errors.append('Username taken')
        
        if errors:
            for e in errors: flash(e, 'error')
            return render_template('auth/signup.html')
        
        user = {
            'username': username.lower(), 'email': email,
            'password': generate_password_hash(password), 'full_name': full_name,
            'avatar': f'https://ui-avatars.com/api/?name={username}&background=6366f1&color=fff',
            'is_admin': users_col.count_documents({}) == 0,
            'created_at': datetime.utcnow(), 'last_login': datetime.utcnow()
        }
        result = users_col.insert_one(user)
        session['user_id'] = str(result.inserted_id)
        session['username'] = username
        streaks_col.insert_one({'user_id': str(result.inserted_id), 'current_streak': 0,
                               'longest_streak': 0, 'last_read_date': None, 'total_reading_days': 0})
        flash('Account created! Welcome to SmartRead!', 'success')
        return redirect(url_for('home'))
    return render_template('auth/signup.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))


# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
def home():
    user = get_current_user()
    
    # If session exists but user doesn't, clear session
    if 'user_id' in session and not user:
        session.clear()
    
    all_books = list(books_col.find({'is_active': True}).sort('created_at', -1))
    
    # Fix cover URLs for books
    for book in all_books:
        if not book.get('cover_url') or not os.path.exists(os.path.join(app.static_folder, book.get('cover_url', '').lstrip('/'))):
            book['cover_url'] = '/static/images/default-cover.svg'
    
    continue_reading, completed_books = [], []
    
    if user:
        for prog in progress_col.find({'user_id': str(user['_id'])}):
            book = books_col.find_one({'_id': ObjectId(prog['book_id'])})
            if book:
                book['progress'] = prog
                book['progress_percent'] = int((len(prog.get('completed_pages', [])) / max(book.get('total_pages', 1), 1)) * 100)
                (completed_books if prog.get('is_completed') else continue_reading).append(book)
        continue_reading.sort(key=lambda x: x['progress'].get('last_read_at', datetime.min), reverse=True)
    
    return render_template('home.html', user=user, all_books=all_books,
                          continue_reading=continue_reading[:10], completed_books=completed_books)


@app.route('/library')
@login_required
def library():
    user = get_current_user()
    books = list(books_col.find({'is_active': True}))
    for book in books:
        progress = progress_col.find_one({'user_id': str(user['_id']), 'book_id': str(book['_id'])})
        if progress:
            book['progress'] = progress
            book['progress_percent'] = int((len(progress.get('completed_pages', [])) / max(book.get('total_pages', 1), 1)) * 100)
    return render_template('books/library.html', user=user, books=books)


@app.route('/book/<book_id>')
@login_required
def book_detail(book_id):
    user = get_current_user()
    book = books_col.find_one({'_id': ObjectId(book_id)})
    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('home'))
    return render_template('books/detail.html', user=user, book=book,
                          progress=get_reading_progress(user['_id'], book_id))


@app.route('/read/<book_id>')
@app.route('/read/<book_id>/<int:page>')
@login_required
def read_book(book_id, page=None):
    user = get_current_user()
    book = books_col.find_one({'_id': ObjectId(book_id)})
    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('home'))
    
    progress = get_reading_progress(user['_id'], book_id)
    page = page or progress.get('current_page', 1)
    
    unlocked_pages = progress.get('unlocked_pages', [1])
    if page not in unlocked_pages and page != 1:
        flash('This page is locked!', 'error')
        page = max(unlocked_pages) if unlocked_pages else 1
    
    pages = book.get('pages', [])
    total_pages = len(pages)
    page = max(1, min(page, total_pages))
    
    content = pages[page - 1] if pages else {'content': 'No content', 'page_number': 1}
    
    quiz_required, quiz_data = False, None
    if page % 3 == 0 and page not in progress.get('completed_pages', []):
        if f"page_{page}" not in progress.get('quiz_scores', {}):
            quiz_required = True
            quiz_pages = pages[max(0, page - 3):page]
            quiz_data = {'questions': generate_quiz_from_content(quiz_pages), 'passing_score': 70}
    
    update_streak(str(user['_id']))
    
    return render_template('books/read.html', user=user, book=book, page=page,
                          total_pages=total_pages, content=content, progress=progress,
                          prev_page=page - 1 if page > 1 else None,
                          next_page=page + 1 if page < total_pages else None,
                          next_page_locked=page + 1 not in unlocked_pages if page < total_pages else False,
                          quiz_required=quiz_required, quiz_data=quiz_data)


# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    user = get_current_user()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    stats = {
        'total_users': users_col.count_documents({}),
        'total_books': books_col.count_documents({}),
        'active_readers': progress_col.count_documents({'last_read_at': {'$gte': today}}),
        'total_quizzes': quiz_results_col.count_documents({})
    }
    return render_template('admin/dashboard.html', user=user, stats=stats,
                          books=list(books_col.find().sort('created_at', -1).limit(10)),
                          recent_users=list(users_col.find().sort('created_at', -1).limit(5)))


@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def upload_book():
    user = get_current_user()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General')
        
        if 'pdf_file' not in request.files:
            flash('No PDF file', 'error')
            return redirect(request.url)
        
        pdf_file = request.files['pdf_file']
        if not pdf_file.filename or not allowed_file(pdf_file.filename):
            flash('Invalid PDF', 'error')
            return redirect(request.url)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        pdf_filename = f"{timestamp}_{secure_filename(pdf_file.filename)}"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'books', pdf_filename)
        pdf_file.save(pdf_path)
        
        pages = extract_pdf_pages(pdf_path)
        if not pages:
            flash('Could not extract text', 'error')
            os.remove(pdf_path)
            return redirect(request.url)
        
        cover_url = '/static/images/default-cover.svg'
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename:
            cover_filename = f"{timestamp}_cover_{secure_filename(cover_file.filename)}"
            cover_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_filename))
            cover_url = f'/static/uploads/covers/{cover_filename}'
        
        books_col.insert_one({
            'title': title, 'author': author, 'description': description, 'category': category,
            'pdf_path': f'/static/uploads/books/{pdf_filename}', 'cover_url': cover_url,
            'pages': pages, 'total_pages': len(pages),
            'total_words': sum(p.get('word_count', 0) for p in pages),
            'is_active': True, 'uploaded_by': str(user['_id']), 'created_at': datetime.utcnow()
        })
        flash(f'"{title}" uploaded with {len(pages)} pages! Quizzes auto-generate.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/upload.html', user=user)


@app.route('/admin/book/<book_id>/quizzes', methods=['GET', 'POST'])
@admin_required
def admin_manage_quizzes(book_id):
    user = get_current_user()
    book = books_col.find_one({'_id': ObjectId(book_id)})
    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/quizzes.html', user=user, book=book,
                          quizzes=list(quizzes_col.find({'book_id': str(book_id)}).sort('after_page', 1)),
                          quiz_pages=[i for i in range(3, book['total_pages'] + 1, 3)])


# ============================================
# API ROUTES
# ============================================

@app.route('/api/streak')
@login_required
def api_get_streak():
    return jsonify(get_user_streak(str(get_current_user()['_id'])))


@app.route('/api/word/<word>')
def api_word_meaning(word):
    result = {'word': word, 'english': None, 'hindi': None, 'marathi': None, 'phonetic': '', 'audio': '', 'examples': []}
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5)
        if r.status_code == 200:
            data = r.json()[0]
            result['phonetic'] = data.get('phonetic', '')
            for p in data.get('phonetics', []):
                if p.get('audio'): result['audio'] = p['audio']; break
            meanings, examples = [], []
            for m in data.get('meanings', [])[:3]:
                for d in m.get('definitions', [])[:2]:
                    meanings.append({'type': m.get('partOfSpeech', ''), 'definition': d.get('definition', '')})
                    if d.get('example'): examples.append(d['example'])
            result['english'], result['examples'] = meanings, examples[:3]
    except: pass
    try:
        r = requests.get(f"https://api.mymemory.translated.net/get?q={word}&langpair=en|hi", timeout=5)
        if r.status_code == 200: result['hindi'] = r.json().get('responseData', {}).get('translatedText', '')
    except: pass
    try:
        r = requests.get(f"https://api.mymemory.translated.net/get?q={word}&langpair=en|mr", timeout=5)
        if r.status_code == 200: result['marathi'] = r.json().get('responseData', {}).get('translatedText', '')
    except: pass
    return jsonify(result)


@app.route('/api/complete-page', methods=['POST'])
@login_required
def api_complete_page():
    user = get_current_user()
    data = request.get_json()
    book_id, page, time_spent = data.get('book_id'), data.get('page'), data.get('time_spent', 0)
    if not book_id or not page:
        return jsonify({'error': 'Missing data'}), 400
    
    result = update_progress(str(user['_id']), book_id, page, time_spent)
    quiz_required, quiz_data = False, None
    
    if page % 3 == 0:
        progress = get_reading_progress(user['_id'], book_id)
        if f"page_{page}" not in progress.get('quiz_scores', {}):
            quiz_required = True
            book = books_col.find_one({'_id': ObjectId(book_id)})
            if book:
                quiz_data = generate_quiz_from_content(book.get('pages', [])[max(0, page-3):page])
    
    return jsonify({'success': True, 'completed': result['completed'], 'unlocked': result['unlocked'],
                   'quiz_required': quiz_required, 'quiz_data': quiz_data})


@app.route('/api/submit-quiz', methods=['POST'])
@login_required
def api_submit_quiz():
    user = get_current_user()
    data = request.get_json()
    book_id, page, answers, questions = data.get('book_id'), data.get('page'), data.get('answers', []), data.get('questions', [])
    
    correct = sum(1 for i, a in enumerate(answers) if i < len(questions) and questions[i].get('correct_index') == a)
    total = len(questions)
    score = int((correct / total) * 100) if total > 0 else 0
    passed = score >= 70
    
    quiz_results_col.insert_one({'user_id': str(user['_id']), 'book_id': book_id, 'page': page,
                                 'score': score, 'passed': passed, 'answers': answers, 'submitted_at': datetime.utcnow()})
    
    if passed:
        progress = get_reading_progress(user['_id'], book_id)
        quiz_scores = progress.get('quiz_scores', {})
        quiz_scores[f"page_{page}"] = score
        progress_col.update_one(
            {'user_id': str(user['_id']), 'book_id': str(book_id)},
            {'$set': {'quiz_scores': quiz_scores,
                      'unlocked_pages': list(set(progress.get('unlocked_pages', [1]) + [page + 1])),
                      'completed_pages': list(set(progress.get('completed_pages', []) + [page]))}}
        )
    
    return jsonify({'success': True, 'score': score, 'passed': passed, 'correct': correct, 'total': total,
                   'message': '🎉 Great job! Next pages unlocked!' if passed else f'{score}% - Need 70% to pass.'})


@app.route('/api/ai-assist', methods=['POST'])
@login_required
def api_ai_assist():
    data = request.get_json()
    content, action = data.get('content', ''), data.get('action', 'summarize')
    if not content:
        return jsonify({'error': 'No content'}), 400
    
    if action == 'summarize':
        sentences = [s.strip() for s in content.split('.')[:3] if s.strip()]
        result = f"📝 **Summary:** {'. '.join(sentences)}."
    elif action == 'key_points':
        sentences = [s.strip() for s in content.split('.')[:5] if len(s.strip()) > 20]
        result = "🔑 **Key Points:**\n" + "\n".join(f"• {s}" for s in sentences)
    else:
        result = f"📖 **Simple Explanation:** {' '.join(content.split()[:30])}..."
    
    return jsonify({'result': result})
from flask import Flask
app = Flask(__name__, static_folder="static", template_folder="templates")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'books'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'covers'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'images'), exist_ok=True)
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║   📚 SmartRead - AI-Powered Book Reading Platform              ║
    ║   Server: http://localhost:5000                                ║
    ║   🔥 NEW: Daily Streak | Auto-Quiz | Better Admin UI           ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)
if __name__ == "__main__":
    app.run()