# Flask Library
from flask import Flask, render_template
from datetime import datetime
import pytz
import os
import tweepy
from dotenv import load_dotenv
import praw
import requests

# Get IST time for logging
def get_ist_time():
    ist = pytz.timezone('Asia/Kolkata')
    ist_time = datetime.now(ist)
    print("🕒 Current IST Time:", ist_time.strftime("%Y-%m-%d %H:%M:%S"))

# Load environment variables
load_dotenv()

# Twitter API setup
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Reddit API setup
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent
)

print("✅ Logged in to Reddit as:", reddit.user.me())

# News API setup
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Fetch tweets
def fetch_tweets():
    try:
        query = "(#Football OR #PremierLeague) lang:en -is:retweet -is:reply"
        response = client.search_recent_tweets(
            query=query,
            max_results=10,
            tweet_fields=['text', 'created_at', 'author_id'],
            expansions=['author_id']
        )

        tweets_data = []
        ist = pytz.timezone('Asia/Kolkata')
        if response.data:
            for tweet in response.data:
                created_at_ist = tweet.created_at.astimezone(ist)
                tweets_data.append({
                    'text': tweet.text,
                    'author': tweet.author_id,
                    'created_at': created_at_ist.strftime("%Y-%m-%d %H:%M:%S")
                })
        return tweets_data

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

# Fetch football news
def fetch_football_news():
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=football OR premier league&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize=5&"
        f"apiKey={NEWS_API_KEY}"
    )
    
    response = requests.get(url)
    data = response.json()
    
    news_list = []
    if data.get("status") == "ok":
        for article in data["articles"]:
            news_list.append({
                'title': article['title'],
                'source': article['source']['name'],
                'url': article['url'],
                'published_at': article['publishedAt']
            })
    else:
        print("⚠️ Failed to fetch news:", data.get("message"))
    
    return news_list

# Fetch Reddit posts about football
def fetch_reddit_posts():
    try:
        reddit_posts = []
        subreddit = reddit.subreddit('soccer')  # You can change the subreddit if needed
        for submission in subreddit.new(limit=5):
            reddit_posts.append({
                'title': submission.title,
                'url': submission.url,
                'created_at': datetime.utcfromtimestamp(submission.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                'author': submission.author.name if submission.author else 'Unknown'
            })
        return reddit_posts
    except Exception as e:
        print(f"❌ Error fetching Reddit posts: {e}")
        return []


# Home route
@app.route("/")
def home():
    tweets = fetch_tweets()
    news = fetch_football_news()
    reddit_posts = fetch_reddit_posts()
    return render_template("index.html", tweets=tweets, news=news,reddit_posts=reddit_posts)

# Run the app
if __name__ == "__main__":
    get_ist_time()
    app.run(debug=True, port=5050)
