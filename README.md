# Daily Drape 🧥✨

> AI-powered outfit recommendation web app — tell it your occasion, weather, and gender, and it styles a complete look for you in seconds.

**Live demo:** [dailydrape-b4dp.onrender.com](https://dailydrape-b4dp.onrender.com)

---

## Overview

Daily Drape kills outfit-decision paralysis. Instead of scrolling through a closet (or a shopping app) wondering what to wear, you pick three things — your **gender**, the **weather**, and the **occasion** — and Daily Drape instantly builds a complete top/bottom/shoes look, paired with an AI-generated editorial-style photo of the outfit.

> *"I used to spend 20 minutes choosing an outfit. Now I spend 20 seconds and look better."*

---

## Features

- 🔐 **Flexible auth** — sign up with name/email/password, or sign in instantly via email OTP (no password required)
- 🎨 **AI-styled looks** — outfit photography generated on the fly via the Pollinations AI image API, with prompts built from the chosen gender/weather/occasion
- 🧵 **24 curated combinations** — 2 genders × 3 weather types × 4 occasions, each mapped to a hand-picked top/bottom/shoes description
- 📸 **Admin-curated photos** — admins can upload real reference photos per combination (up to 3 slots each); these are served in place of AI images when available, with Pillow-based resizing/compression for consistent quality
- 🔁 **Try Alternative** — swap to a different outfit suggestion for the same criteria without reloading the page
- ❤️ **Favorites** — save looks you like to a personal wardrobe
- ⭐ **Feedback & ratings** — rate any generated look (1–5 stars) with optional comments, and revisit your own feedback history
- 📊 **Admin dashboard** — usage stats, per-combo photo coverage, recent logins, and recent feedback at a glance
- 🔍 **Lightbox zoom**, animated background, and a fully responsive, mobile-first UI

---

## Tech Stack

| Layer            | Technology                                                              |
|-------------------|--------------------------------------------------------------------------|
| Backend           | Flask (Python)                                                          |
| Database          | PostgreSQL (hosted on [Neon](https://neon.tech)) via SQLAlchemy ORM     |
| Templating        | Jinja2                                                                  |
| Auth              | Werkzeug password hashing + email OTP                                  |
| Email delivery    | [Brevo](https://www.brevo.com/) transactional email **HTTPS REST API**  |
| AI image gen      | [Pollinations.ai](https://pollinations.ai) text-to-image API           |
| Image processing  | Pillow (resize/compress AI + admin-uploaded photos)                    |
| Deployment        | Render (Gunicorn)                                                       |

**Why Brevo's REST API instead of `smtplib`?** Render's free tier blocks outbound SMTP ports, which silently breaks OTP email delivery. Switching to Brevo's HTTPS API sidesteps the port restriction entirely since it just makes a normal web request.

---

## Getting Started

### Prerequisites
- Python 3.11+
- A PostgreSQL database (Neon, Render Postgres, or local Postgres all work)
- A free [Brevo](https://www.brevo.com/) account + API key (for sending OTP emails)

### Installation

```bash
git clone https://github.com/vishwajambu02/daily-drape.git
cd daily-drape
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-flask-secret-key
DATABASE_URL=postgresql://user:password@host:5432/daily_drape
BREVO_API_KEY=your-brevo-api-key
MAIL_USERNAME=your-sender-email@example.com
ADMIN_SECRET=your-admin-secret
```

### Run locally

```bash
python app.py
```

The app will be available at `http://localhost:5000`.

---

## Project Structure

```
daily-drape/
├── app.py                 # Flask routes, auth, outfit logic, admin endpoints
├── models.py               # SQLAlchemy models (User, Outfit, Feedback, etc.)
├── templates/               # Jinja2 HTML templates (login, result, favorites, feedback, admin)
├── static/
│   └── outfits/             # Admin-uploaded reference photos
└── requirements.txt
```

---

## Deployment

Currently deployed on **[Render](https://render.com)**, with the live database hosted on **Neon**. The app runs behind Gunicorn (`gunicorn app:app`).

---

## Roadmap

- [ ] Outfit history with a calendar view
- [ ] Personalized styling based on past likes/ratings
- [ ] Social sharing of generated looks
- [ ] Open Graph meta tags for richer link previews

---

## Author

Built by **Vishwa Jambu** — third-year B.Tech CSE student, Parul University.

- GitHub: [@vishwajambu02](https://github.com/vishwajambu02)
- LinkedIn: [vishwa-jambu](https://www.linkedin.com/in/vishwa-jambu-7a007039b/)

---

## License

This project is currently unlicensed / all rights reserved. *(Add an MIT/Apache license here if you want others to freely reuse the code.)*
