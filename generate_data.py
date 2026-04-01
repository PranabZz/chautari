import pandas as pd
import random
import os
from datetime import datetime, timedelta

# Configuration
NUM_USERS = 150
NUM_POSTS = 1200
NUM_FRIENDSHIPS = 2000
NUM_ENGAGEMENTS = 5000

CATEGORIES = ["tech", "gaming", "music", "cooking", "fashion", "science", "sports", "travel", "art", "news"]
CONTENT_TYPES = ["video", "image", "text"]
LOCATIONS = ["New York", "San Francisco", "Chicago", "Los Angeles", "London", "Berlin", "Boston", "Nashville", "Manchester", "Paris", "Tokyo", "Sydney"]

def generate_data():
    os.makedirs('data', exist_ok=True)
    
    # 1. Users
    users = []
    for i in range(1, NUM_USERS + 1):
        # Last 5 users are "New Users" (Cold Start)
        if i > (NUM_USERS - 5):
            prefs = "" 
            username = f"new_user_{i}"
        else:
            prefs = ",".join(random.sample(CATEGORIES, k=random.randint(1, 3)))
            username = f"user_{i}"
            
        users.append({
            "user_id": i,
            "username": username,
            "age": random.randint(18, 60),
            "location": random.choice(LOCATIONS),
            "preferences": prefs
        })
    pd.DataFrame(users).to_csv('data/users.csv', index=False)
    print(f"Generated {NUM_USERS} users (Last 5 are Cold-Start).")

    # 2. Friendships
    friendships = set()
    # Only create friendships for the first 145 users
    while len(friendships) < NUM_FRIENDSHIPS:
        u1 = random.randint(1, NUM_USERS - 5)
        u2 = random.randint(1, NUM_USERS - 5)
        if u1 != u2:
            pair = tuple(sorted((u1, u2)))
            friendships.add(pair)
    
    friendship_list = [{"user_id_1": f[0], "user_id_2": f[1], "since_date": "2024-01-01"} for f in friendships]
    pd.DataFrame(friendship_list).to_csv('data/friendships.csv', index=False)
    print(f"Generated {NUM_FRIENDSHIPS} friendships.")

    # 3. Posts
    posts = []
    now = datetime.now()
    for i in range(1, NUM_POSTS + 1):
        c_type = random.choice(CONTENT_TYPES)
        created_at = now - timedelta(days=random.randint(0, 13), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        posts.append({
            "post_id": 1000 + i,
            "user_id": random.randint(1, NUM_USERS - 5), # New users haven't posted yet
            "content_type": c_type,
            "category": random.choice(CATEGORIES),
            "duration_sec": random.randint(15, 600) if c_type == "video" else 0,
            "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    pd.DataFrame(posts).to_csv('data/posts.csv', index=False)
    print(f"Generated {NUM_POSTS} posts.")

    # 4. Engagements
    engagements = []
    seen_pairs = set()
    while len(engagements) < NUM_ENGAGEMENTS:
        uid = random.randint(1, NUM_USERS - 5) # New users have no history
        pid = 1000 + random.randint(1, NUM_POSTS)
        if (uid, pid) not in seen_pairs:
            post = posts[pid - 1001]
            liked = 1 if random.random() > 0.4 else 0
            commented = 1 if random.random() > 0.7 else 0
            shared = 1 if random.random() > 0.8 else 0
            
            watch_time = 0
            if post["content_type"] == "video":
                watch_time = int(post["duration_sec"] * random.uniform(0.1, 1.1))
            
            engagements.append({
                "user_id": uid,
                "post_id": pid,
                "liked": liked,
                "commented": commented,
                "shared": shared,
                "watch_time_sec": watch_time
            })
            seen_pairs.add((uid, pid))
    
    pd.DataFrame(engagements).to_csv('data/engagements.csv', index=False)
    print(f"Generated {NUM_ENGAGEMENTS} engagements.")

if __name__ == "__main__":
    generate_data()
