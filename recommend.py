import pandas as pd
import os
import sys
from collections import Counter

def load_data():
    data_dir = 'data'
    users = pd.read_csv(os.path.join(data_dir, 'users.csv'))
    friendships = pd.read_csv(os.path.join(data_dir, 'friendships.csv'))
    posts = pd.read_csv(os.path.join(data_dir, 'posts.csv'))
    engagements = pd.read_csv(os.path.join(data_dir, 'engagements.csv'))
    return users, friendships, posts, engagements

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
    for friend_id in direct_friends:
        fof.discard(friend_id)
    return list(fof), direct_friends

def calculate_recommendations(user_id, users, friendships, posts, engagements):
    user_row = users[users['user_id'] == user_id].iloc[0]
    user_prefs = [p.strip() for p in str(user_row['preferences']).split(',')]
    
    fof_ids, direct_friends = get_friends_of_friends(user_id, friendships)
    
    # 1. Map Friend Preferences (What categories do my friends like?)
    friend_pref_list = []
    for f_id in direct_friends:
        f_prefs = users[users['user_id'] == f_id]['preferences'].iloc[0]
        friend_pref_list.extend([p.strip() for p in str(f_prefs).split(',')])
    friend_pref_counts = Counter(friend_pref_list)

    # 2. Map FoF Preferences
    fof_pref_list = []
    for f_id in fof_ids:
        f_prefs = users[users['user_id'] == f_id]['preferences'].iloc[0]
        fof_pref_list.extend([p.strip() for p in str(f_prefs).split(',')])
    fof_pref_counts = Counter(fof_pref_list)

    # Base engagement
    eng_with_posts = engagements.merge(posts[['post_id', 'duration_sec']], on='post_id')
    eng_with_posts['watch_ratio'] = eng_with_posts.apply(
        lambda row: (row['watch_time_sec'] / row['duration_sec']) if row['duration_sec'] > 0 else 0, axis=1
    )
    eng_with_posts['score'] = (
        eng_with_posts['liked'] * 10 + 
        eng_with_posts['commented'] * 20 + 
        eng_with_posts['shared'] * 30 + 
        eng_with_posts['watch_ratio'] * 40
    )
    
    avg_scores = eng_with_posts.groupby('post_id')['score'].mean().reset_index()
    recommendations = posts.merge(avg_scores, on='post_id', how='left').fillna(0)
    
    friends_interactions = engagements[engagements['user_id'].isin(direct_friends)]['post_id'].unique()

    def compute_final_score_and_reasons(row):
        score = row['score'] # Base trending score
        reasons = []
        
        # PRIORITY 1: User Preferences
        if row['category'] in user_prefs:
            score += 200 
            reasons.append(f"Matches your interest in {row['category']}")
            
        # PRIORITY 2: User's Friend Authored
        if row['user_id'] in direct_friends:
            score += 150
            creator_name = users[users['user_id'] == row['user_id']]['username'].values[0]
            reasons.append(f"Posted by your friend @{creator_name}")
            
        # PRIORITY 3: User's Friend Interacted
        if row['post_id'] in friends_interactions:
            score += 100
            reasons.append("Your friends are interacting with this")

        # PRIORITY 4: User's Friends Preferences (Social Interest)
        if friend_pref_counts[row['category']] > 0:
            boost = min(friend_pref_counts[row['category']] * 10, 80)
            score += boost
            reasons.append(f"Popular category among your friends")

        # PRIORITY 5: FoF Authored
        if row['user_id'] in fof_ids:
            score += 60
            reasons.append("Posted by someone in your extended network")
            
        # PRIORITY 6: FoF Preferences
        if fof_pref_counts[row['category']] > 0:
            boost = min(fof_pref_counts[row['category']] * 5, 40)
            score += boost
            reasons.append(f"Trending in your extended network")
            
        if not reasons:
            reasons.append("Suggested for you")
            
        return pd.Series([score, " • ".join(reasons)], index=['final_score', 'reasons'])

    res = recommendations.apply(compute_final_score_and_reasons, axis=1)
    recommendations['final_score'] = res['final_score']
    recommendations['reasons'] = res['reasons']
    
    engaged_posts = engagements[engagements['user_id'] == user_id]['post_id'].tolist()
    recommendations = recommendations[~recommendations['post_id'].isin(engaged_posts)]
    
    return recommendations.sort_values(by='final_score', ascending=False)

def display_post(post_row, users, index, total):
    creator = users[users['user_id'] == post_row['user_id']].iloc[0]
    os.system('clear' if os.name == 'posix' else 'cls')
    print("\n" + "═"*60)
    print(f"   SOCIAL FEED ({index + 1} / {total})")
    print("═"*60)
    print(f"\n👤 @{creator['username']} ({creator['location']})")
    print(f"📂 Category: {post_row['category'].upper()}")
    print(f"📝 Type: {post_row['content_type'].capitalize()}")
    if post_row['content_type'] == 'video':
        print(f"⏱️ Duration: {post_row['duration_sec']} seconds")
    print("\n" + "─"*60)
    print(f"✨ WHY YOU'RE SEEING THIS:")
    # Split reasons to show priority hierarchy
    reasons = post_row['reasons'].split(" • ")
    for r in reasons:
        print(f"   ✅ {r}")
    print("─"*60)
    print(f"\n[Post ID: {post_row['post_id']} | Reco-Score: {post_row['final_score']:.1f}]")
    print("\n" + "═"*60)
    print(" [n] Next Post  |  [p] Previous Post  |  [q] Exit to Menu")
    print("═"*60)

def main():
    users, friendships, posts, engagements = load_data()
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n" + "═"*50)
        print("   RECO-SYSTEM: PRIORITIZED FEED")
        print("═"*50)
        print("Select a user to view their personalized feed:")
        sample_users = users.sample(10).sort_values('user_id')
        for _, row in sample_users.iterrows():
            print(f"  {row['user_id']:>3}. @{row['username']:<15} | Prefs: {row['preferences']}")
        choice = input("\nEnter User ID (or 'q' to quit): ")
        if choice.lower() == 'q':
            break
        try:
            user_id = int(choice)
            if user_id not in users['user_id'].values:
                print("Invalid User ID.")
                input("Press Enter to continue...")
                continue
            recs = calculate_recommendations(user_id, users, friendships, posts, engagements)
            recs_list = recs.to_dict('records')
            if not recs_list:
                print("\nNo recommendations available.")
                input("Press Enter to continue...")
                continue
            current_idx = 0
            while True:
                display_post(recs_list[current_idx], users, current_idx, len(recs_list))
                nav = input("\n>> ").lower()
                if nav == 'n' and current_idx < len(recs_list) - 1:
                    current_idx += 1
                elif nav == 'p' and current_idx > 0:
                    current_idx -= 1
                elif nav == 'q':
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
