import snscrape.modules.twitter as sntwitter

tweet_id = "1987088612115067291"
tweet = next(sntwitter.TwitterTweetScraper(tweet_id).get_items())
print(tweet.content)
