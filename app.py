import os, random, string, urllib.parse
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone, timedelta
from flask import render_template, redirect, url_for, session
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from flask_mail import Mail, Message
from models import db, User, LoginLog, Outfit, OutfitLike, Feedback, AlternativeClick
from werkzeug.security import generate_password_hash, check_password_hash


# ──────────────────────────────────────────────
# APP CONFIG
# ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/daily_drape")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

app.config['MAIL_SERVER']         = 'smtp-relay.brevo.com'
app.config['MAIL_PORT']           = 465
app.config['MAIL_USE_TLS']        = False
app.config['MAIL_USE_SSL']        = True
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('Daily Drape', os.environ.get('MAIL_USERNAME'))

# Outfit image upload config
OUTFIT_IMG_FOLDER = os.path.join("static", "outfits")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_PHOTO_SLOTS = 3
os.makedirs(OUTFIT_IMG_FOLDER, exist_ok=True)

db.init_app(app)
mail = Mail(app)

# ── Startup env-var debug (safe — only shows True/False, not values) ──
print(f"[STARTUP] MAIL_USERNAME set: {bool(os.environ.get('MAIL_USERNAME'))}", flush=True)
print(f"[STARTUP] MAIL_PASSWORD set: {bool(os.environ.get('MAIL_PASSWORD'))}", flush=True)
print(f"[STARTUP] MAIL_SERVER: {app.config['MAIL_SERVER']}", flush=True)
print(f"[STARTUP] MAIL_PORT: {app.config['MAIL_PORT']}", flush=True)

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "dailydrape-admin-2024")

ALL_COMBOS = [
    ("female", "hot",   "college"),
    ("female", "hot",   "date"),
    ("female", "hot",   "party"),
    ("female", "hot",   "wedding"),
    ("female", "cold",  "college"),
    ("female", "cold",  "date"),
    ("female", "cold",  "party"),
    ("female", "cold",  "wedding"),
    ("female", "rainy", "college"),
    ("female", "rainy", "date"),
    ("female", "rainy", "party"),
    ("female", "rainy", "wedding"),
    ("male",   "hot",   "college"),
    ("male",   "hot",   "date"),
    ("male",   "hot",   "party"),
    ("male",   "hot",   "wedding"),
    ("male",   "cold",  "college"),
    ("male",   "cold",  "date"),
    ("male",   "cold",  "party"),
    ("male",   "cold",  "wedding"),
    ("male",   "rainy", "college"),
    ("male",   "rainy", "date"),
    ("male",   "rainy", "party"),
    ("male",   "rainy", "wedding"),
]

OUTFITS = {
    ("female","hot","college"):  ("Graphic Tee Cropped",            "Cargo Mini Skirt",                "White Sneakers"),
    ("female","hot","date"):     ("Sheer Floral Blouse",            "-",                           "Block-Heel Sandals"),
    ("female","hot","party"):    ("Satin Slip Dress in Champagne",  "–",                               "Strappy Heeled Mules"),
    ("female","hot","wedding"):  ("Embroidered Anarkali Suit",      "–",                               "Kolhapuri Heels"),
    ("female","cold","college"): ("Hoodie + Puffer Vest",           "Jogger Pants",                    "Chunky Sneakers"),
    ("female","cold","date"):    ("Cashmere Turtleneck Rust",       "Faux Leather Midi Skirt",         "Chelsea Boots"),
    ("female","cold","party"):   ("Velvet Off-Shoulder Mini Dress", "–",                               "Ankle Boots"),
    ("female","cold","wedding"): ("Silk Lehenga with Dupatta",      "–",                               "Embellished Heels"),
    ("female","rainy","college"):("Waterproof Trench Coat",         "Slim Fit Jeans",                  "Rubber Chelsea Boots"),
    ("female","rainy","date"):   ("Belted Raincoat Rust",           "Slim Ankle Trousers",             "Waterproof Ankle Boots"),
    ("female","rainy","party"):  ("Sequin Top with Rain Shell",     "–",                               "Platform Rain Boots"),
    ("female","rainy","wedding"):("Silk Lehenga with Rain Cape",    "–",                               "Embellished Waterproof Heels"),
    ("male","hot","college"):    ("Graphic Tee",                    "Jogger Shorts",                   "Chunky Sneakers"),
    ("male","hot","date"):       ("Fitted Polo Shirt White",        "Slim Chinos Beige",               "White Sneakers"),
    ("male","hot","party"):      ("Silk Printed Camp Shirt",        "Tailored Trousers in Black",      "Leather Loafers"),
    ("male","hot","wedding"):    ("Sherwani in Ivory",              "–",                               "Mojari Shoes"),
    ("male","cold","college"):   ("Puffer Jacket + Hoodie",         "Jogger Pants",                    "Chunky Sneakers"),
    ("male","cold","date"):      ("Crewneck Sweater in Burgundy",   "Dark Slim Jeans",                 "Leather Boots"),
    ("male","cold","party"):     ("Turtleneck Merino Black",        "Tailored Trousers",               "Chelsea Boots"),
    ("male","cold","wedding"):   ("Bandhgala Suit in Navy",         "–",                               "Embroidered Shoes"),
    ("male","rainy","college"):  ("Waterproof Windbreaker",         "Slim Cargo Pants",                "Waterproof Boots"),
    ("male","rainy","date"):     ("Trench Coat Dark Navy",          "Slim Fit Trousers",               "Water-Resistant Derbies"),
    ("male","rainy","party"):    ("Quilted Bomber with Rain Shell", "Tailored Trousers",               "Waterproof Leather Boots"),
    ("male","rainy","wedding"):  ("Bandhgala with Rain Cape",       "–",                               "Waterproof Embroidered Shoes"),
}


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def now_utc():
    return datetime.now(timezone.utc)

def get_client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def generate_otp(length=6):
    return "".join(random.choices(string.digits, k=length))

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_uploaded_photo_slots(gender, weather, occasion):
    key = f"{gender}_{weather}_{occasion}"
    slots = []
    for slot_num in range(1, MAX_PHOTO_SLOTS + 1):
        for ext in ALLOWED_EXTENSIONS:
            path = os.path.join(OUTFIT_IMG_FOLDER, f"{key}_{slot_num}.{ext}")
            if os.path.exists(path):
                slots.append(f"/static/outfits/{key}_{slot_num}.{ext}")
                break
    return slots

def get_pollinations_url(gender, weather, occasion):
    top, bottom, shoes = OUTFITS.get((gender, weather, occasion),
                                     ("Classic Linen Shirt", "Tailored Trousers", "Clean Leather Shoes"))
    bottom_text = "no separate bottom, one-piece outfit" if bottom == "–" else bottom
    prompt = (
        f"Editorial fashion photograph of a {gender} model wearing "
        f"{top}, {bottom_text}, and {shoes}. "
        f"Styled for a {occasion} occasion in {weather} weather. "
        f"Clean studio background, soft natural lighting, full-body shot, "
        f"high-fashion magazine quality."
    )
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=400&nologo=true&model=flux"

def pick_outfit_image(gender, weather, occasion, exclude_url=None):
    slots = get_uploaded_photo_slots(gender, weather, occasion)
    if not slots:
        return get_pollinations_url(gender, weather, occasion), False
    if exclude_url and len(slots) > 1:
        candidates = [s for s in slots if s != exclude_url]
    else:
        candidates = slots
    chosen = random.choice(candidates)
    return chosen, True


# ──────────────────────────────────────────────
# CREATE TABLES
# ──────────────────────────────────────────────
with app.app_context():
    db.create_all()


# ──────────────────────────────────────────────
# AUTH ROUTES
# ──────────────────────────────────────────────
@app.route("/login", methods=["GET"])
def login():
    if current_user():
        return redirect(url_for("index"))
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 5.0
    total_outfits = Outfit.query.count()
    return render_template("login.html", avg_rating=avg_rating, total_outfits=total_outfits)


# ── SIGN UP ───────────────────────────────────
@app.route("/signup", methods=["POST"])
def signup():
    name     = request.form.get("name",             "").strip()
    phone    = request.form.get("phone",            "").strip() or None
    email    = request.form.get("email",            "").strip().lower()
    password = request.form.get("password",         "")
    confirm  = request.form.get("confirm_password", "")

    if not name:
        flash("Please enter your name.", "error")
        return redirect(url_for("login") + "?tab=signup")

    if not email or "@" not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("login") + "?tab=signup")

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("login") + "?tab=signup")

    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("login") + "?tab=signup")

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("An account with that email already exists. Sign in instead.", "warning")
        return redirect(url_for("login") + "?tab=signin")

    user = User(
        name=name,
        phone=phone,
        email=email,
        created_at=now_utc()
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    user.last_login_at = now_utc()
    db.session.add(LoginLog(
        user_id=user.id,
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string,
        method="PASSWORD",
        success=True,
        logged_at=now_utc()
    ))
    db.session.commit()

    session.clear()
    session["user_id"] = user.id
    flash(f"Welcome to Daily Drape, {name}! 🎉", "success")
    return redirect(url_for("index"))


# ── PASSWORD LOGIN ────────────────────────────
@app.route("/login-password", methods=["POST"])
def login_password():
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No account found with that email. Create one in the Sign Up tab.", "error")
        return redirect(url_for("login") + "?tab=signin")

    if not user.password_hash:
        flash("You haven't set a password yet. Sign in with Email OTP, then set one from your home screen.", "warning")
        return redirect(url_for("login") + "?tab=otp")

    if not user.check_password(password):
        db.session.add(LoginLog(
            user_id=user.id, ip_address=get_client_ip(),
            user_agent=request.user_agent.string,
            method="PASSWORD", success=False, logged_at=now_utc()
        ))
        db.session.commit()
        flash("Incorrect password. Try again or use Email OTP.", "error")
        return redirect(url_for("login") + "?tab=signin")

    user.last_login_at = now_utc()
    db.session.add(LoginLog(
        user_id=user.id, ip_address=get_client_ip(),
        user_agent=request.user_agent.string,
        method="PASSWORD", success=True, logged_at=now_utc()
    ))
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    return redirect(url_for("index"))


# ── SET PASSWORD ──────────────────────────────
@app.route("/set-password", methods=["GET", "POST"])
@login_required
def set_password():
    user = current_user()

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("set_password"))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("set_password"))

        user.set_password(password)
        db.session.commit()
        flash("Password saved! You can now sign in with it anytime.", "success")
        return redirect(url_for("index"))

    return render_template("set_password.html", user=user)


# ── SET USERNAME ──────────────────────────────
@app.route("/set-username", methods=["POST"])
@login_required
def set_username():
    user = current_user()
    name = request.form.get("name", "").strip()

    if not name:
        flash("Name can't be empty.", "error")
        return redirect(url_for("index"))

    if len(name) > 100:
        flash("Name must be under 100 characters.", "error")
        return redirect(url_for("index"))

    user.name = name
    db.session.commit()
    flash(f"Welcome, {name}! Your name has been saved.", "success")
    return redirect(url_for("index"))


# ── SEND OTP ──────────────────────────────────
@app.route("/send-otp", methods=["POST"])
def send_otp():
    import threading
    import traceback

    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Please enter a valid email.", "error")
        return redirect(url_for("login"))

    otp = generate_otp()
    exp = now_utc() + timedelta(minutes=10)
    session["otp_email"]   = email
    session["otp_code"]    = otp
    session["otp_expires"] = exp.isoformat()

    print(f"\n{'='*40}", flush=True)
    print(f"  OTP for {email}  -->  {otp}", flush=True)
    print(f"{'='*40}\n", flush=True)

   def send_async_email(to_email, otp_code):
    import requests as req
    print("[EMAIL] Thread started", flush=True)
    try:
        api_key = os.environ.get("BREVO_API_KEY")
        print(f"[EMAIL] API key set: {bool(api_key)}", flush=True)
        response = req.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"name": "Daily Drape", "email": "vishwajambu66@gmail.com"},
                "to": [{"email": to_email}],
                "subject": "Your Daily Drape OTP",
                "textContent": (
                    f"Hi,\n\n"
                    f"Your Daily Drape OTP is: {otp_code}\n\n"
                    f"Valid for 10 minutes.\n\n"
                    f"- Daily Drape Team"
                )
            }
        )
        print(f"[EMAIL] Status: {response.status_code}", flush=True)
        print(f"[EMAIL] Response: {response.text}", flush=True)
        if response.status_code == 201:
            print("[EMAIL] ✅ Email sent successfully!", flush=True)
        else:
            print(f"[EMAIL] ❌ Failed: {response.text}", flush=True)
    except Exception as e:
        print(f"[EMAIL] ❌ Exception: {e}", flush=True)


# ── OTP VERIFY ────────────────────────────────
@app.route("/verify-otp", methods=["GET"])
def verify_otp_page():
    return render_template("verify.html", dev_otp=None)


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    entered = request.form.get("otp", "").strip()
    email   = session.get("otp_email")
    code    = session.get("otp_code")
    exp_str = session.get("otp_expires")

    if not (email and code and exp_str):
        flash("Session expired. Please try again.", "error")
        return redirect(url_for("login"))

    exp = datetime.fromisoformat(exp_str)
    if now_utc() > exp:
        flash("OTP expired. Please request a new one.", "error")
        return redirect(url_for("login"))

    if entered != code:
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.add(LoginLog(
                user_id=user.id, ip_address=get_client_ip(),
                user_agent=request.user_agent.string,
                method="OTP", success=False, logged_at=now_utc()
            ))
            db.session.commit()
        flash("Incorrect OTP.", "error")
        return redirect(url_for("verify_otp_page"))

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, created_at=now_utc())
        db.session.add(user)
        db.session.flush()

    user.last_login_at = now_utc()
    db.session.add(LoginLog(
        user_id=user.id, ip_address=get_client_ip(),
        user_agent=request.user_agent.string,
        method="OTP", success=True, logged_at=now_utc()
    ))
    db.session.commit()

    session.pop("otp_email",   None)
    session.pop("otp_code",    None)
    session.pop("otp_expires", None)
    session["user_id"] = user.id
    return redirect(url_for("index"))


# ── LOGOUT ────────────────────────────────────
@app.route("/logout")
def logout():
    user = current_user()
    if user:
        last_login = (LoginLog.query
                      .filter_by(user_id=user.id, success=True)
                      .filter(LoginLog.logged_out_at.is_(None))
                      .order_by(LoginLog.logged_at.desc())
                      .first())
        if last_login:
            last_login.logged_out_at = now_utc()
            db.session.commit()
    session.clear()
    return redirect(url_for("login"))


# ──────────────────────────────────────────────
# MAIN PAGES
# ──────────────────────────────────────────────
@app.route("/", methods=["GET"])
@login_required
def index():
    user = current_user()
    has_password = bool(user.password_hash)
    has_username = bool(user.name)

    avg_rating    = db.session.query(func.avg(Feedback.rating)).scalar()
    avg_rating    = round(avg_rating, 1) if avg_rating else 0.0
    total_outfits = Outfit.query.count()
    total_users   = User.query.count()

    return render_template("index.html",
                           user=user,
                           has_password=has_password,
                           has_username=has_username,
                           avg_rating=avg_rating,
                           total_outfits=total_outfits,
                           total_users=total_users)


@app.route("/result", methods=["POST"])
@login_required
def result():
    user     = current_user()
    occasion = request.form.get("occasion", "casual")
    weather  = request.form.get("weather",  "hot")
    gender   = request.form.get("gender",   "female")

    key     = (gender, weather, occasion)
    default = ("Classic Linen Shirt", "Tailored Trousers", "Clean Leather Shoes")
    top, bottom, shoes = OUTFITS.get(key, default)

    image_url, is_uploaded = pick_outfit_image(gender, weather, occasion)

    outfit = Outfit(
        occasion=occasion, weather=weather, gender=gender,
        top=top, bottom=bottom, shoes=shoes,
        image_url=image_url,
        user_id=user.id if user else None,
        generated_at=now_utc()
    )
    db.session.add(outfit)
    db.session.commit()

    session["last_shown_image"] = image_url

    return render_template("result.html",
        outfit=outfit,
        criteria={"occasion": occasion, "weather": weather, "gender": gender},
        image=image_url,
        is_uploaded=is_uploaded,
        is_liked=False
    )


# ──────────────────────────────────────────────
# FAVORITES
# ──────────────────────────────────────────────
@app.route("/favorites")
@login_required
def favorites():
    user = current_user()
    liked_ids = db.session.query(OutfitLike.outfit_id)\
        .filter_by(user_id=user.id, liked=True).subquery()
    outfits = Outfit.query.filter(Outfit.id.in_(liked_ids))\
        .order_by(Outfit.generated_at.desc()).all()
    return render_template("favorites.html", outfits=outfits, user=user)


# ──────────────────────────────────────────────
# FEEDBACK PAGE
# ──────────────────────────────────────────────
@app.route("/feedback-page")
@login_required
def feedback_page():
    user = current_user()
    feedbacks = Feedback.query.filter_by(user_id=user.id)\
        .order_by(Feedback.submitted_at.desc()).limit(20).all()
    return render_template("feedback.html", feedbacks=feedbacks, user=user)


# ──────────────────────────────────────────────
# API: LIKE
# ──────────────────────────────────────────────
@app.route("/like", methods=["POST"])
@login_required
def like_outfit():
    user      = current_user()
    outfit_id = request.form.get("outfit_id", type=int)
    Outfit.query.get_or_404(outfit_id)
    existing  = OutfitLike.query.filter_by(user_id=user.id, outfit_id=outfit_id)\
        .order_by(OutfitLike.liked_at.desc()).first()
    new_state = not (existing and existing.liked)
    db.session.add(OutfitLike(
        user_id=user.id, outfit_id=outfit_id,
        liked=new_state, liked_at=now_utc()
    ))
    db.session.commit()
    return jsonify({"liked": new_state, "outfit_id": outfit_id})


# ──────────────────────────────────────────────
# API: ALTERNATIVE OUTFIT
# ──────────────────────────────────────────────
@app.route("/alternative", methods=["POST"])
@login_required
def alternative():
    user      = current_user()
    outfit_id = request.form.get("outfit_id", type=int)
    occasion  = request.form.get("occasion", "casual")
    weather   = request.form.get("weather",  "hot")
    gender    = request.form.get("gender",   "female")

    ALTS = [
        ("Oversized Sage Linen Shirt",    "Straight Leg Cream Trousers",   "White Leather Loafers"),
        ("Cropped White Cotton Tee",      "Pleated Maxi Skirt Terracotta", "Espadrille Wedge Sandals"),
        ("Sleeveless Floral Wrap Top",    "Linen Paperbag Shorts Beige",   "Platform Slide Sandals"),
        ("Striped Breton Tee",            "Wide Leg Jeans Light Wash",     "Ballet Flats Nude"),
        ("Off-Shoulder Smocked Blouse",   "Tiered Midi Skirt",             "Strappy Flat Sandals"),
    ]
    top, bottom, shoes = random.choice(ALTS)

    last_shown = session.get("last_shown_image")
    image_url, is_uploaded = pick_outfit_image(gender, weather, occasion, exclude_url=last_shown)

    new_outfit = Outfit(
        occasion=occasion, weather=weather, gender=gender,
        top=top, bottom=bottom, shoes=shoes,
        image_url=image_url,
        user_id=user.id if user else None,
        generated_at=now_utc()
    )
    db.session.add(new_outfit)
    db.session.flush()

    db.session.add(AlternativeClick(
        outfit_id=outfit_id, user_id=user.id if user else None,
        occasion=occasion, weather=weather, gender=gender,
        new_outfit_id=new_outfit.id, clicked_at=now_utc()
    ))
    db.session.commit()

    session["last_shown_image"] = image_url

    return jsonify({
        "outfit_id":   new_outfit.id,
        "top":         new_outfit.top,
        "bottom":      new_outfit.bottom,
        "shoes":       new_outfit.shoes,
        "image":       new_outfit.image_url,
        "is_uploaded": is_uploaded
    })


# ──────────────────────────────────────────────
# API: FEEDBACK SUBMIT
# ──────────────────────────────────────────────
@app.route("/feedback", methods=["POST"])
def feedback():
    user      = current_user()
    outfit_id = request.form.get("outfit_id", type=int)
    rating    = request.form.get("rating",    type=int)
    name      = request.form.get("name",      "").strip()
    phone     = request.form.get("phone",     "").strip() or None
    comments  = request.form.get("comments",  "").strip() or None

    if not outfit_id or not rating or not (1 <= rating <= 5):
        return jsonify({"error": "Invalid data"}), 400

    db.session.add(Feedback(
        outfit_id=outfit_id,
        user_id=user.id if user else None,
        name=name or None, phone=phone,
        rating=rating, comments=comments,
        submitted_at=now_utc()
    ))
    db.session.commit()
    return jsonify({"success": True})


# ──────────────────────────────────────────────
# ADMIN: UPLOAD OUTFIT IMAGE
# ──────────────────────────────────────────────
@app.route("/admin/upload-outfit", methods=["POST"])
def upload_outfit_image():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user_obj = db.session.get(User, user_id)
    if not user_obj or not user_obj.is_admin:
        return jsonify({"error": "Admin only"}), 403

    gender   = request.form.get("gender",   "").strip()
    weather  = request.form.get("weather",  "").strip()
    occasion = request.form.get("occasion", "").strip()
    slot     = request.form.get("slot", "1").strip()
    file     = request.files.get("image")

    if not all([gender, weather, occasion, file]):
        return jsonify({"error": "Missing fields"}), 400
    if slot not in {"1", "2", "3"}:
        return jsonify({"error": "Slot must be 1, 2, or 3"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only jpg, jpeg, png, webp allowed"}), 400

    ext      = file.filename.rsplit(".", 1)[1].lower()
    base_key = f"{gender}_{weather}_{occasion}_{slot}"
    filename = f"{base_key}.{ext}"

    for old_ext in ALLOWED_EXTENSIONS:
        old_path = os.path.join(OUTFIT_IMG_FOLDER, f"{base_key}.{old_ext}")
        if os.path.exists(old_path):
            os.remove(old_path)

    file.save(os.path.join(OUTFIT_IMG_FOLDER, filename))
    return jsonify({"success": True, "url": f"/static/outfits/{filename}", "slot": slot})


@app.route("/admin/delete-outfit-photo", methods=["POST"])
def delete_outfit_photo():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user_obj = db.session.get(User, user_id)
    if not user_obj or not user_obj.is_admin:
        return jsonify({"error": "Admin only"}), 403

    gender   = request.form.get("gender",   "").strip()
    weather  = request.form.get("weather",  "").strip()
    occasion = request.form.get("occasion", "").strip()
    slot     = request.form.get("slot", "").strip()

    if not all([gender, weather, occasion, slot]) or slot not in {"1", "2", "3"}:
        return jsonify({"error": "Missing or invalid fields"}), 400

    base_key = f"{gender}_{weather}_{occasion}_{slot}"
    removed = False
    for ext in ALLOWED_EXTENSIONS:
        path = os.path.join(OUTFIT_IMG_FOLDER, f"{base_key}.{ext}")
        if os.path.exists(path):
            os.remove(path)
            removed = True

    return jsonify({"success": True, "removed": removed})


# ──────────────────────────────────────────────
# ADMIN DASHBOARD
# ──────────────────────────────────────────────
@app.route("/admin")
def admin():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    current_user_obj = db.session.get(User, user_id)
    if not current_user_obj:
        return redirect(url_for("login"))

    is_admin = bool(current_user_obj.is_admin)

    total_users           = User.query.count()
    total_recommendations = Outfit.query.count()
    total_likes           = OutfitLike.query.filter_by(liked=True).count()
    total_feedback        = Feedback.query.count()

    occasion_rows  = db.session.query(Outfit.occasion, func.count(Outfit.id)).group_by(Outfit.occasion).all()
    occasion_stats = [(occ or "unknown", count) for occ, count in occasion_rows]

    gender_rows  = db.session.query(Outfit.gender, func.count(Outfit.id)).group_by(Outfit.gender).all()
    gender_stats = [(g or "unknown", count) for g, count in gender_rows]

    weather_rows  = db.session.query(Outfit.weather, func.count(Outfit.id)).group_by(Outfit.weather).all()
    weather_stats = [(w or "unknown", count) for w, count in weather_rows]

    feedback_rows = Feedback.query.order_by(Feedback.id.desc()).limit(50).all()
    feedbacks     = [(f.name, f.rating, f.comments) for f in feedback_rows]

    recent_logins  = LoginLog.query.order_by(LoginLog.logged_at.desc()).limit(50).all()
    recent_outfits = Outfit.query.order_by(Outfit.id.desc()).limit(50).all()

    combo_status = []
    for (gender, weather, occasion) in ALL_COMBOS:
        key = f"{gender}_{weather}_{occasion}"
        slot_urls = {}
        for slot_num in range(1, MAX_PHOTO_SLOTS + 1):
            slot_urls[slot_num] = None
            for ext in ALLOWED_EXTENSIONS:
                path = os.path.join(OUTFIT_IMG_FOLDER, f"{key}_{slot_num}.{ext}")
                if os.path.exists(path):
                    slot_urls[slot_num] = f"/static/outfits/{key}_{slot_num}.{ext}"
                    break

        top, bottom, shoes = OUTFITS.get((gender, weather, occasion), ("–", "–", "–"))
        filled_count = sum(1 for v in slot_urls.values() if v)
        combo_status.append({
            "gender":       gender,
            "weather":      weather,
            "occasion":     occasion,
            "key":          key,
            "top":          top,
            "bottom":       bottom,
            "shoes":        shoes,
            "slot_urls":    slot_urls,
            "filled_count": filled_count,
        })

    uploaded_count       = sum(1 for c in combo_status if c["filled_count"] > 0)
    fully_uploaded_count = sum(1 for c in combo_status if c["filled_count"] == MAX_PHOTO_SLOTS)

    return render_template(
        "admin.html",
        is_admin=is_admin,
        total_users=total_users,
        total_recommendations=total_recommendations,
        total_likes=total_likes,
        total_feedback=total_feedback,
        occasion_stats=occasion_stats,
        gender_stats=gender_stats,
        weather_stats=weather_stats,
        feedbacks=feedbacks,
        recent_logins=recent_logins,
        recent_outfits=recent_outfits,
        combo_status=combo_status,
        uploaded_count=uploaded_count,
        fully_uploaded_count=fully_uploaded_count,
        total_combos=len(ALL_COMBOS),
        max_photo_slots=MAX_PHOTO_SLOTS,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
