# Freelancer Scout Skill

> Helps Full-stack PM/Engineers find and pitch high-value "0-1" projects.

## 🎯 Core Value Proposition

**"One-Person Army"**
You don't just write code; you define the product, design the architecture, and ship the MVP.
This tool identifies clients who need *speed* and *autonomy* rather than just a pair of hands.

## 📋 Features

- **Hybrid Analysis**: Scores projects based on both Technical (Next.js, Python) and Product (MVP, Roadmap) keywords.
- **Pain Point Detection**: Identifies clients with "Fuzzy Requirements", "Missing CTO", or "Legacy Debt".
- **Smart Verification**: Validates emails and URLs in real-time to ensure leads are fresh.
- **Automated Outreach**: Generates personalized drafts positioning you as a Technical Partner, not just a freelancer.

## 🚀 Usage

```bash
# Test with mock data
python3 scout.py --test

# Search with Exa AI (requires API Key)
export EXA_API_KEY="your-key-here"
python3 scout.py --query "looking for mvp developer"

# Search with Brave (Good for freshness)
export BRAVE_API_KEY="your-brave-key"
python3 scout.py --query "site:upwork.com/jobs mvp" --provider brave --freshness pw

# Or pass key directly
python3 scout.py --query "looking for mvp developer" --api-key "your-key-here"
```

## 🛠 Configuration

Edit `profile.py` to update your:
- Tech Stack (currently: Next.js + FastAPI)
- Highlight Projects (for dynamic email insertion)
- Pitch Angle
