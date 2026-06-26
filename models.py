# models.py  –  Daily Drape  –  PostgreSQL schema via SQLAlchemy

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def now_utc():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────
# 1. USERS  (sign-up / login tracking)
# ─────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone         = db.Column(db.String(20),  nullable=True)
    name          = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)

    # timestamps
    created_at    = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_admin      = db.Column(db.Boolean, default=False, nullable=False)

    # relationships
    login_logs   = db.relationship("LoginLog",         back_populates="user", lazy="dynamic")
    outfit_likes = db.relationship("OutfitLike",        back_populates="user", lazy="dynamic")
    feedbacks    = db.relationship("Feedback",          back_populates="user", lazy="dynamic")
    alt_clicks   = db.relationship("AlternativeClick",  back_populates="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


# ─────────────────────────────────────────────
# 2. LOGIN LOGS  (every sign-in / sign-out event)
# ─────────────────────────────────────────────
class LoginLog(db.Model):
    __tablename__ = "login_logs"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    ip_address    = db.Column(db.String(45),  nullable=True)
    user_agent    = db.Column(db.Text,        nullable=True)
    method        = db.Column(db.String(20),  default="OTP")
    success       = db.Column(db.Boolean,     default=True)
    logged_at     = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    logged_out_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="login_logs")

    def __repr__(self):
        return f"<LoginLog user={self.user_id} at={self.logged_at}>"


# ─────────────────────────────────────────────
# 3. OUTFITS  (AI-generated outfits)
# ─────────────────────────────────────────────
class Outfit(db.Model):
    __tablename__ = "outfits"

    id           = db.Column(db.Integer, primary_key=True)
    occasion     = db.Column(db.String(100), nullable=False)
    weather      = db.Column(db.String(100), nullable=False)
    gender       = db.Column(db.String(50),  nullable=False)
    top          = db.Column(db.Text, nullable=False)
    bottom       = db.Column(db.Text, nullable=False)
    shoes        = db.Column(db.Text, nullable=False)
    image_url    = db.Column(db.Text, nullable=True)
    generated_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    likes      = db.relationship("OutfitLike",       back_populates="outfit", lazy="dynamic")
    feedbacks  = db.relationship("Feedback",         back_populates="outfit", lazy="dynamic")
    alt_clicks = db.relationship("AlternativeClick", foreign_keys="AlternativeClick.outfit_id",
                                 back_populates="outfit", lazy="dynamic")

    def __repr__(self):
        return f"<Outfit {self.id} {self.occasion}>"


# ─────────────────────────────────────────────
# 4. OUTFIT LIKES  (wardrobe saves)
# ─────────────────────────────────────────────
class OutfitLike(db.Model):
    __tablename__ = "outfit_likes"

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey("users.id"),   nullable=True,  index=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    liked     = db.Column(db.Boolean, default=True)
    liked_at  = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

    user   = db.relationship("User",   back_populates="outfit_likes")
    outfit = db.relationship("Outfit", back_populates="likes")

    def __repr__(self):
        return f"<OutfitLike outfit={self.outfit_id} liked={self.liked}>"


# ─────────────────────────────────────────────
# 5. FEEDBACK  (star rating + comments)
# ─────────────────────────────────────────────
class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id           = db.Column(db.Integer, primary_key=True)
    outfit_id    = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"),   nullable=True,  index=True)
    name         = db.Column(db.String(150), nullable=True)
    phone        = db.Column(db.String(20),  nullable=True)
    rating       = db.Column(db.SmallInteger, nullable=False)
    comments     = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

    outfit = db.relationship("Outfit", back_populates="feedbacks")
    user   = db.relationship("User",   back_populates="feedbacks")

    def __repr__(self):
        return f"<Feedback outfit={self.outfit_id} rating={self.rating}>"


# ─────────────────────────────────────────────
# 6. ALTERNATIVE CLICKS
# ─────────────────────────────────────────────
class AlternativeClick(db.Model):
    __tablename__ = "alternative_clicks"

    id            = db.Column(db.Integer, primary_key=True)
    outfit_id     = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"),   nullable=True,  index=True)
    occasion      = db.Column(db.String(100), nullable=True)
    weather       = db.Column(db.String(100), nullable=True)
    gender        = db.Column(db.String(50),  nullable=True)
    new_outfit_id = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=True)
    clicked_at    = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

    outfit     = db.relationship("Outfit", foreign_keys=[outfit_id],     back_populates="alt_clicks")
    new_outfit = db.relationship("Outfit", foreign_keys=[new_outfit_id])
    user       = db.relationship("User",   back_populates="alt_clicks")

    def __repr__(self):
        return f"<AlternativeClick outfit={self.outfit_id} at={self.clicked_at}>"