import pandas as pd
import os
import sys
from collections import Counter
from datetime import datetime
import numpy as np

def load_data():
    data_dir = 'data'
    users = pd.read_csv(os.path.join(data_dir, 'users.csv'))
    friendships = pd.read_csv(os.path.join(data_dir, 'friendships.csv'))
    posts = pd.read_csv(os.path.join(data_dir, 'posts.csv'))
    engagements = pd.read_csv(os.path.join(data_dir, 'engagements.csv'))
    return users, friendships, posts, engagements

def save_engagement(user_id, post_id, action):
    df = pd.read_csv('data/engagements.csv')
    mask = (df['user_id'] == user_id) & (df['post_id'] == post_id)
    if mask.any():
        if action == 'like': df.loc[mask, 'liked'] = 1
        elif action == 'comment': df.loc[mask, 'commented'] = 1
    else:
        new_row = {'user_id': user_id, 'post_id': post_id, 'liked': 1 if action == 'like' else 0,
                  'commented': 1 if action == 'comment' else 0, 'shared': 0, 'watch_time_sec': 0}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv('data/engagements.csv', index=False)

def get_friends(user_id, friendships):
    f1 = friendships[friendships['user_id_1'] == user_id]['user_id_2'].tolist()
    f2 = friendships[friendships['user_id_2'] == user_id]['user_id_1'].tolist()
    return list(set(f1 + f2))

def get_friends_of_friends(user_id, friendships):
    direct_friends = get_friends(user_id, friendships)
    fof = set()
    for friend_id in direct_friends:
        ff = get_friends(friend_id, friendships)
        fof.update(ff)
    fof.discard(user_id)
    for friend_id in direct_friends: fof.discard(friend_id)
    return list(fof), direct_friends

def apply_diversity_filter(df, penalty_factor=0.7):
    sorted_df = df.sort_values(by='final_score', ascending=False).copy()
    category_counts = {}
    diversified_scores = []
    for _, row in sorted_df.iterrows():
        cat = row['category']; count = category_counts.get(cat, 0)
        penalty = np.power(penalty_factor, count)
        diversified_scores.append(row['final_score'] * penalty)
        category_counts[cat] = count + 1
    sorted_df['final_score'] = diversified_scores
    return sorted_df.sort_values(by='final_score', ascending=False)

def calculate_recommendations(user_id, users, friendships, posts, engagements):
    user_row = users[users['user_id'] == user_id].iloc[0]
    raw_prefs = str(user_row['preferences']).strip()
    user_prefs = [p.strip() for p in raw_prefs.split(',')] if raw_prefs and raw_prefs != 'nan' else []
    
    fof_ids, direct_friends = get_friends_of_friends(user_id, friendships)
    
    # Check if this is a "Cold Start" user
    is_cold_start = len(user_prefs) == 0 and len(direct_friends) == 0

    # 1. Map Social Preferences
    friend_pref_counts = Counter()
    for f_id in direct_friends:
        f_prefs = str(users[users['user_id'] == f_id]['preferences'].iloc[0])
        if f_prefs != 'nan': friend_pref_counts.update([p.strip() for p in f_prefs.split(',')])

    # 2. Base engagement (Global Trending logic)
    eng_with_posts = engagements.merge(posts[['post_id', 'duration_sec']], on='post_id')
    eng_with_posts['watch_ratio'] = eng_with_posts.apply(
        lambda row: (row['watch_time_sec'] / row['duration_sec']) if row['duration_sec'] > 0 else 0, axis=1
    )
    eng_with_posts['score'] = (
        eng_with_posts['liked'] * 10 + eng_with_posts['commented'] * 20 + 
        eng_with_posts['shared'] * 30 + eng_with_posts['watch_ratio'] * 40
    )
    
    avg_scores = eng_with_posts.groupby('post_id')['score'].mean().reset_index()
    recommendations = posts.merge(avg_scores, on='post_id', how='left').fillna(0)
    
    friends_interactions = engagements[engagements['user_id'].isin(direct_friends)]['post_id'].unique()

    now = datetime.now()
    recommendations['created_at'] = pd.to_datetime(recommendations['created_at'])
    recommendations['age_hours'] = (now - recommendations['created_at']).dt.total_seconds() / 3600

    def compute_final_score_and_reasons(row):
        score = row['score'] # Start with global trending score
        reasons = []
        
        # Priority Logic
        if row['category'] in user_prefs:
            score += 200; reasons.append(f"Matches your interest in {row['category']}")
            
        if row['user_id'] in direct_friends:
            score += 150; reasons.append(f"Posted by your friend")
            
        if row['post_id'] in friends_interactions:
            score += 100; reasons.append("Your friends liked this")

        if friend_pref_counts[row['category']] > 0:
            score += min(friend_pref_counts[row['category']] * 10, 80)
            reasons.append(f"Popular with your friends")

        if is_cold_start:
            # For new users, we boost the global trending score significantly 
            # to ensure they see high-quality content first.
            score += row['score'] * 2 
            reasons.append("Trending globally")

        decay_factor = 1.0 / (np.power(row['age_hours'] + 2, 0.5))
        final_score = score * decay_factor
        
        age_str = "Just now" if row['age_hours'] < 1 else (f"{int(row['age_hours'])}h ago" if row['age_hours'] < 24 else f"{int(row['age_hours']/24)}d ago")
        reasons.insert(0, f"New post ({age_str})")

        return pd.Series([final_score, " • ".join(reasons), age_str], index=['final_score', 'reasons', 'age_str'])

    res = recommendations.apply(compute_final_score_and_reasons, axis=1)
    recommendations['final_score'] = res['final_score']
    recommendations['reasons'] = res['reasons']
    recommendations['age_str'] = res['age_str']
    
    liked_posts = engagements[(engagements['user_id'] == user_id) & (engagements['liked'] == 1)]['post_id'].tolist()
    recommendations = recommendations[~recommendations['post_id'].isin(liked_posts)]
    
    return apply_diversity_filter(recommendations)

def display_post(post_row, users, index, total, user_id, engagements):
    creator = users[users['user_id'] == post_row['user_id']].iloc[0]
    status = engagements[(engagements['user_id'] == user_id) & (engagements['post_id'] == post_row['post_id'])]
    is_liked = "❤️ Liked" if not status.empty and status['liked'].iloc[0] == 1 else "🤍 Like"
    is_commented = "💬 Commented" if not status.empty and status['commented'].iloc[0] == 1 else "🗨️ Comment"

    os.system('clear' if os.name == 'posix' else 'cls')
    print("\n" + "═"*60)
    print(f"   SANJAL FEED ({index + 1} / {total})")
    print("═"*60)
    print(f"\n👤 @{creator['username']}  •  📅 {post_row['age_str']}")
    print(f"📂 Category: {post_row['category'].upper()}")
    print(f"📝 Type: {post_row['content_type'].capitalize()}")
    print("\n" + "─"*60)
    print(f"✨ WHY YOU'RE SEEING THIS:")
    for r in post_row['reasons'].split(" • "): print(f"   ✅ {r}")
    print("─"*60)
    print(f"\n[Post ID: {post_row['post_id']} | Final-Score: {post_row['final_score']:.1f}]")
    print("\n" + "═"*60)
    print(f" [L] Like  |  [C] Comment  |  [N] Next  |  [P] Prev  |  [Q] Exit")
    print("═"*60)

def main():
    while True:
        users, friendships, posts, engagements = load_data()
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n" + "═"*50); print("   SANJAL: SMART SOCIAL FEED"); print("═"*50)
        print("Pick a user (146-150 are NEW users):")
        sample_users = pd.concat([users.head(5), users.tail(5)])
        for _, row in sample_users.iterrows():
            print(f"  {row['user_id']:>3}. @{row['username']:<15} | Prefs: {row['preferences'] if str(row['preferences']) != 'nan' else 'None'}")
        
        choice = input("\nEnter User ID (or 'q' to quit): ")
        if choice.lower() == 'q': break
        try:
            user_id = int(choice)
            if user_id not in users['user_id'].values: continue
            recs = calculate_recommendations(user_id, users, friendships, posts, engagements)
            recs_list = recs.to_dict('records')
            current_idx = 0
            while True:
                display_post(recs_list[current_idx], users, current_idx, len(recs_list), user_id, engagements)
                nav = input("\n>> ").lower()
                if nav == 'l': save_engagement(user_id, recs_list[current_idx]['post_id'], 'like'); _, _, _, engagements = load_data()
                elif nav == 'c': save_engagement(user_id, recs_list[current_idx]['post_id'], 'comment'); _, _, _, engagements = load_data()
                elif nav == 'n' and current_idx < len(recs_list) - 1: current_idx += 1
                elif nav == 'p' and current_idx > 0: current_idx -= 1
                elif nav == 'q': break
        except Exception as e: print(f"Error: {e}"); input("Press Enter...")

if __name__ == "__main__": main()
