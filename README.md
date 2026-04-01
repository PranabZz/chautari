# 🚀 Social Recommendation System Architecture

This project demonstrates a multi-stage recommendation engine using a **Hybrid Collaborative + Content-Based** approach.

## 🏗️ Production Data Pipeline

In a real-world application (like Instagram or TikTok), the system would follow this high-level architecture:

### 1. Data Collection (Ingestion)
*   **Behavioral Events:** Real-time stream (Kafka/RabbitMQ) capturing every Like, Comment, and Share.
*   **Video Heartbeats:** Tracking `watch_time` every 5 seconds to calculate completion rates.
*   **Graph Updates:** Neo4j or a similar Graph Database to manage friendships and "Friends-of-Friends" (FoF) queries at scale.

### 2. Feature Store (The "Brain")
Instead of reading CSVs, the system queries a **Feature Store** (e.g., Redis, Feast) to get:
*   **User Embeddings:** A numerical "summary" of what a user likes.
*   **Post Embeddings:** A numerical "summary" of what the post is about.
*   **Social Context:** Pre-computed lists of friends and FoF interactions.

### 3. Recommendation Pipeline (The "Engine")
We use a **Two-Stage** approach to ensure the app stays fast even with millions of posts:

#### Stage A: Retrieval (The "Funnel")
*   **Goal:** Reduce 1,000,000+ posts to the best 500 candidates in < 100ms.
*   **Heuristics:**
    *   Last 24h posts from **Direct Friends**.
    *   Top 100 posts matching **User Preferences**.
    *   Trending posts in the user's **Location**.
    *   Posts liked by **Friends-of-Friends**.

#### Stage B: Ranking (The "Judge")
*   **Goal:** Precisely sort the 500 candidates.
*   **Model:** A Deep Learning model (e.g., Neural Collaborative Filtering or XGBoost) predicts the probability of engagement.
*   **Priority Hierarchy:**
    1.  User Preferences (Weight: 1.0)
    2.  Friend Content (Weight: 0.8)
    3.  Friend Interactions (Weight: 0.6)
    4.  FoF Content/Interests (Weight: 0.3)

### 4. Serving (The "App")
*   **API Layer:** FastAPI or Go service that calls the Ranking Model.
*   **Caching:** The top 50 recommendations are cached in Redis for immediate delivery.
*   **Pagination:** Using `n` (next) and `p` (prev) logic to stream the ranked list to the user's device.

---

## 🛠️ Current Prototype Structure

This prototype simulates the **Ranking Stage** using weighted heuristics:

*   `data/`: CSV-based mock of a production database.
*   `generate_data.py`: Data generator creating a social graph of 150 users and 1,200 posts.
*   `recommend.py`: The interactive terminal "App" that implements the priority-based ranking logic.

### Priority Logic in this Prototype:
1.  **User Preferences (+200 pts)**
2.  **Friend's Posts (+150 pts)**
3.  **Friend Interactions (+100 pts)**
4.  **Friend Interests (+10 pts/friend)**
5.  **FoF Content (+60 pts)**
6.  **FoF Interests (+5 pts/FoF)**

---

## 🚀 How to Run

1. **Setup Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install pandas
   ```

2. **Generate Fresh Data:**
   ```bash
   python generate_data.py
   ```

3. **Launch the Social Feed:**
   ```bash
   python recommend.py
   ```
