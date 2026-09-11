# X Growth Hub

Reverse-engineer Twitter/X growth strategies. Analyze any profile, score tweets, find winning patterns, and clone successful tactics for your own account.

## Features

- **Analyze Profile**: Scrape any X/Twitter profile and score all tweets using engagement formula
- **Compare Accounts**: Side-by-side comparison of multiple accounts' performance
- **My Account Audit**: Analyze your own account, get personalized recommendations
- **Tweet Scoring**: Score = (Replies×20) + (Reposts×2) + (Likes×0.5) + (Bookmarks×80)

## Tech Stack

- **Frontend**: Next.js 16 + shadcn/ui + Tailwind CSS
- **Backend**: Flask API (Python) - tweet analysis service
- **Deployment**: Vercel (frontend) + Render/Railway (backend API)

## Getting Started

### Frontend (Next.js)
```bash
npm install
npm run dev
```

### Backend (Flask)
```bash
cd ../follower-dashboard
python app.py
```

### Environment
```bash
# Copy the example env
cp env.example.txt .env.local
# Update NEXT_PUBLIC_API_BASE to point to your Flask backend
```

## Deployment

Deploy the frontend to Vercel with one click:
```bash
vercel
```

## License

MIT
