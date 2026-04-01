# 🌳 Chautari (चौतारी)

**Chautari** is a social-first recommendation engine prototype. It simulates how modern social media platforms (like Instagram or TikTok) decide which posts to show you by balancing **personal interests**, **social connections**, and **content freshness**.

---

## 🧐 What is this?
This project is a **Hybrid Recommendation System**. It doesn't just look at what you like; it looks at who your friends are, what they like, and how "hot" a post is globally. It uses a **Two-Stage Ranking Pipeline**:
1.  **Heuristic Scoring:** Assigning points based on social and interest matches.
2.  **Dynamic Filtering:** Applying "Time Decay" (to keep the feed fresh) and "Diversity Filters" (to prevent repetitive content).

---

## 🧠 The "Why" Behind the Algorithm

| Factor | Points | The "Why" (Strategy) |
| :--- | :--- | :--- |
| **User Preferences** | **+200** | **Content Filtering:** If you say you like "Tech," we prioritize it. This is the core "hook" to keep you engaged. |
| **Friend Authored** | **+150** | **Social Graph:** Social media is about people. You are most likely to care about what your actual friends are posting. |
| **Friend Interacted** | **+100** | **Social Proof:** If your friends liked a post, it acts as a "vouch" for that content, making it safer to recommend to you. |
| **Social Trends** | **+10/friend** | **Community Interest:** If 5 of your friends all like "Gaming," there is a high probability you will find that category interesting too. |
| **FoF Content** | **+60** | **Network Expansion:** Recommending "Friends of Friends" helps you discover new people within your trusted circle. |
| **Global Trending** | **Variable** | **Popularity:** High-quality content (lots of likes/shares) is boosted to ensure even new users see great posts. |

---

## ⚙️ The Core Engines

### 1. The Freshness Engine (Time Decay)
**Why?** Users hate seeing the same "top" post for three days.
**How:** We use a `Square Root Decay` formula. As a post gets older (in hours), its score is aggressively reduced. This allows a new post with fewer likes to "jump" over an old post with many likes.

### 2. The Diversity Engine (Anti-Bubble)
**Why?** Showing 10 "Tech" posts in a row leads to "boredom fatigue."
**How:** Every time the algorithm picks a post of a certain category, it applies a **30% penalty** to all other posts in that same category. This forces the feed to "mix in" other interests like Music or Art.

### 3. The Cold-Start Engine
**Why?** New users have no friends or preferences. A blank screen is a "churn" point.
**How:** If a user is new, we ignore social scores and apply a **2x multiplier** to the "Global Trending" score. We show them the best of the whole platform until they start liking things.

---

## 🚀 Getting Started

1.  **Install Dependencies:** `pip install pandas numpy`
2.  **Initialize Database:** `python generate_data.py` (Creates 150 users and 1,200 posts)
3.  **Enter the Chautari:** `python recommend.py`

### 🎮 Controls
- `[L]` to **Like** (Immediately updates the engine's data)
- `[C]` to **Comment**
- `[N]` / `[P]` to **Navigate** the ranked feed
- `[Q]` to **Quit** to user selection
