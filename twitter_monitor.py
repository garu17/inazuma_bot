import os
import asyncio
from typing import Dict, Set, List
from datetime import datetime
import tweepy
from discord import Client, TextChannel


class TwitterMonitor:
    def __init__(self, client: Client, check_interval: int = 300):
        """
        Initialize Twitter Monitor optimized for Free Plan
        
        Args:
            client: Discord client instance
            check_interval: Time in seconds between checks (default: 300 = 5 min, recommended for free plan)
        """
        self.client = client
        self.check_interval = check_interval
        self.last_tweet_ids: Dict[str, int] = {}  # Store last tweet ID per user
        self.twitter_api = None
        self.user_ids_cache: Dict[str, str] = {}  # Cache username -> user_id
        self._setup_twitter_api()
    
    def _setup_twitter_api(self) -> None:
        """Setup Twitter API v2 client using Bearer Token (optimized for free plan)"""
        try:
            bearer_token: str = os.getenv('TWITTER_BEARER_TOKEN', '')
            
            if not bearer_token or bearer_token == 'tu_bearer_token':
                print('⚠️ ERROR: TWITTER_BEARER_TOKEN not configured in .env')
                print('   Get it from: https://developer.twitter.com/en/portal/dashboard')
                return
            
            self.twitter_api = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
            print('✅ Twitter API v2 configured (Free Plan optimized)')
        except Exception as e:
            print(f'❌ Error setting up Twitter API: {e}')
    
    async def monitor_twitter(self) -> None:
        """Main monitoring loop - optimized for free plan rate limits"""
        if not self.twitter_api:
            print('❌ Twitter API not configured. Skipping Twitter monitoring.')
            return
        
        usernames_str: str = os.getenv('TWITTER_USERNAMES_TO_MONITOR', '')
        channel_id_str: str = os.getenv('DISCORD_CHANNEL_ID', '')
        check_interval_str: str = os.getenv('TWITTER_CHECK_INTERVAL', '300')
        
        if not usernames_str or usernames_str == 'usuario1,usuario2,usuario3':
            print('⚠️ Warning: TWITTER_USERNAMES_TO_MONITOR not configured in .env')
            return
        
        if not channel_id_str or channel_id_str == 'tu_channel_id':
            print('⚠️ Warning: DISCORD_CHANNEL_ID not configured in .env')
            return
        
        # Parse usernames
        usernames: List[str] = [u.strip() for u in usernames_str.split(',')]
        
        try:
            check_interval: int = int(check_interval_str)
        except ValueError:
            check_interval = 300
            print(f'⚠️ Invalid TWITTER_CHECK_INTERVAL, using default 300 seconds')
        
        try:
            channel_id: int = int(channel_id_str)
        except ValueError:
            print(f'❌ Error: DISCORD_CHANNEL_ID must be a number, got: {channel_id_str}')
            return
        
        print(f'🐦 Twitter Monitor started (Free Plan)')
        print(f'📊 Monitoring {len(usernames)} users: {", ".join(usernames)}')
        print(f'⏱️  Check interval: {check_interval} seconds')
        print(f'📢 Channel ID: {channel_id}')
        
        while True:
            try:
                # Wait for Discord to be ready
                if not self.client.user:
                    print('⏳ Waiting for Discord connection...')
                    await asyncio.sleep(5)
                    continue
                
                # Get the Discord channel - try multiple ways
                channel: TextChannel = self.client.get_channel(channel_id)
                
                if not channel:
                    # Try fetching if get_channel fails
                    try:
                        channel = await self.client.fetch_channel(channel_id)
                        print(f'✅ Channel found via fetch: {channel.name}')
                    except Exception as e:
                        print(f'❌ Cannot find channel {channel_id}: {e}')
                        print(f'   Make sure the bot has access to this channel')
                        await asyncio.sleep(check_interval)
                        continue
                
                if not channel:
                    print(f'❌ Channel {channel_id} still not found')
                    await asyncio.sleep(check_interval)
                    continue
                
                # Check each user for new tweets
                for username in usernames:
                    try:
                        await self._check_and_post_tweets(username, channel)
                    except Exception as e:
                        print(f'❌ Error checking @{username}: {e}')
                
            except Exception as e:
                print(f'❌ Error in monitoring loop: {e}')
            
            await asyncio.sleep(check_interval)
    
    async def _get_user_id(self, username: str) -> str:
        """Get user ID from username (cached to save API calls)"""
        if username in self.user_ids_cache:
            return self.user_ids_cache[username]
        
        try:
            user = self.twitter_api.get_user(username=username)
            if user and user.data:
                user_id = user.data['id']
                self.user_ids_cache[username] = user_id
                return user_id
        except Exception as e:
            print(f'❌ Error getting user ID for @{username}: {e}')
        
        return None
    
    async def _check_and_post_tweets(self, username: str, channel: TextChannel) -> None:
        """Check for new tweets and post them to Discord"""
        try:
            # Get user ID (cached)
            user_id = await self._get_user_id(username)
            if not user_id:
                print(f'❌ User @{username} not found')
                return
            
            # Get the last tweet ID we've seen from this user
            since_id = self.last_tweet_ids.get(username)
            
            # Get recent tweets - optimized for free plan (only get what we need)
            params = {
                'max_results': 10,
                'tweet_fields': ['created_at', 'public_metrics'],
                'user_fields': ['username']
            }
            
            if since_id:
                params['since_id'] = since_id
            
            tweets = self.twitter_api.get_users_tweets(user_id, **params)
            
            if not tweets or not tweets.data:
                return
            
            # Process tweets in reverse order (oldest first)
            for tweet in reversed(tweets.data):
                tweet_id = tweet['id']
                tweet_text = tweet['text']
                
                # ⭐ FILTRO: Si contiene #spoilersie, ignorar el tweet
                if '#spoilersie' in tweet_text.lower():
                    print(f'⏭️  Skipping tweet from @{username} (contains #spoilersie): {tweet_id}')
                    self.last_tweet_ids[username] = tweet_id
                    continue
                
                # Update last seen tweet ID
                self.last_tweet_ids[username] = tweet_id
                
                # Post to Discord
                tweet_url = f'https://twitter.com/{username}/status/{tweet_id}'
                
                message = (
                    f'🐦 **New tweet from @{username}**\n\n'
                    f'{tweet_text}\n\n'
                    f'[View on Twitter]({tweet_url})'
                )
                
                await channel.send(message)
                print(f'✅ Posted tweet from @{username}: {tweet_id}')
        
        except tweepy.TweepyException as e:
            if '429' in str(e):  # Rate limit
                print(f'⚠️  Rate limited. Waiting until reset...')
            else:
                print(f'❌ Twitter API error: {e}')
        except Exception as e:
            print(f'❌ Error checking tweets from @{username}: {e}')


async def start_twitter_monitoring(client: Client) -> None:
    """Start the Twitter monitoring task"""
    check_interval_str: str = os.getenv('TWITTER_CHECK_INTERVAL', '300')
    try:
        check_interval: int = int(check_interval_str)
    except ValueError:
        check_interval = 300
    
    monitor = TwitterMonitor(client, check_interval=check_interval)
    await monitor.monitor_twitter()
