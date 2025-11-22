import os
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime
import tweepy
from discord import Client, TextChannel, Embed, Color


class TwitterMonitor:
    def __init__(self, client: Client, check_interval: int = 7200):
        """
        Initialize Twitter Monitor optimized for Free Plan
        
        Args:
            client: Discord client instance
            check_interval: Time in seconds between checks (default: 7200 = 2 hours, REQUIRED for free plan)
        """
        self.client = client
        self.check_interval = check_interval
        self.last_tweet_ids: Dict[str, int] = {}  # Store last tweet ID per user
        self.twitter_api = None
        self.user_ids_cache: Dict[str, str] = {}  # Cache username -> user_id
        self.usernames_to_monitor: List[str] = []
        self.initialized = False
        self._setup_twitter_api()
    
    def _setup_twitter_api(self) -> None:
        """Setup Twitter API v2 client using Bearer Token (optimized for free plan)"""
        try:
            bearer_token: str = os.getenv('TWITTER_BEARER_TOKEN', '').strip()
            
            # NO decodificar - tweepy lo maneja automáticamente
            # Si el token viene del dashboard con %2F y %3D, déjalo así
            
            if not bearer_token or bearer_token == 'tu_bearer_token':
                print('❌ [SETUP] ERROR: TWITTER_BEARER_TOKEN not configured in .env')
                print('❌ [SETUP] Get it from: https://developer.twitter.com/en/portal/dashboard')
                print('❌ [SETUP] Instructions:')
                print('   1. Go to https://developer.twitter.com/en/portal/dashboard')
                print('   2. Select your app')
                print('   3. Go to "Keys and tokens"')
                print('   4. Copy the "Bearer Token" (paste it exactly as copied)')
                return
            
            print(f'🔧 [SETUP] Bearer token found: {bearer_token[:30]}...')
            print(f'🔧 [SETUP] Token length: {len(bearer_token)} characters')
            
            self.twitter_api = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=False)
            print('✅ [SETUP] Twitter API v2 configured successfully')
        except Exception as e:
            print(f'❌ [SETUP] Error setting up Twitter API: {e}')
    
    async def monitor_twitter(self) -> None:
        """Main monitoring loop - optimized for free plan rate limits"""
        print('\n' + '='*60)
        print('[MONITOR] Starting Twitter Monitor initialization')
        print('='*60)
        
        if not self.twitter_api:
            print('❌ [MONITOR] Twitter API not configured. Stopping monitoring.')
            return
        
        # Load configuration from .env
        usernames_str: str = os.getenv('TWITTER_USERNAMES_TO_MONITOR', '').strip()
        channel_id_str: str = os.getenv('DISCORD_CHANNEL_ID', '').strip()
        check_interval_str: str = os.getenv('TWITTER_CHECK_INTERVAL', '3600').strip()
        
        print(f'📋 [MONITOR] Config loaded from .env:')
        print(f'   TWITTER_USERNAMES_TO_MONITOR = {usernames_str}')
        print(f'   DISCORD_CHANNEL_ID = {channel_id_str}')
        print(f'   TWITTER_CHECK_INTERVAL = {check_interval_str}')
        
        # Validate configuration
        if not usernames_str or usernames_str == 'usuario1,usuario2,usuario3':
            print('❌ [MONITOR] TWITTER_USERNAMES_TO_MONITOR not properly configured!')
            return
        
        if not channel_id_str or channel_id_str == 'tu_channel_id':
            print('❌ [MONITOR] DISCORD_CHANNEL_ID not properly configured!')
            return
        
        # Parse usernames
        self.usernames_to_monitor = [u.strip() for u in usernames_str.split(',')]
        print(f'✅ [MONITOR] Parsed {len(self.usernames_to_monitor)} usernames: {self.usernames_to_monitor}')
        
        # Parse check interval
        try:
            check_interval: int = int(check_interval_str)
            print(f'✅ [MONITOR] Check interval set to {check_interval} seconds ({check_interval/60:.1f} minutes)')
        except ValueError:
            check_interval = 3600
            print(f'⚠️  [MONITOR] Invalid TWITTER_CHECK_INTERVAL, defaulting to 3600 seconds')
        
        # Parse channel ID
        try:
            channel_id: int = int(channel_id_str)
            print(f'✅ [MONITOR] Discord channel ID: {channel_id}')
        except ValueError:
            print(f'❌ [MONITOR] Invalid DISCORD_CHANNEL_ID: {channel_id_str}')
            return
        
        print('='*60)
        print('[MONITOR] Starting monitoring loop...')
        print('='*60 + '\n')
        
        cycle_count = 0
        
        while True:
            cycle_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f'\n{"="*60}')
            print(f'[CYCLE {cycle_count}] Starting at {timestamp}')
            print(f'{"="*60}')
            
            try:
                # Wait for Discord to be ready
                if not self.client.user:
                    print(f'⏳ [CYCLE {cycle_count}] Discord not ready yet. Waiting...')
                    await asyncio.sleep(5)
                    continue
                
                print(f'✅ [CYCLE {cycle_count}] Discord connected as {self.client.user}')
                
                # Get the Discord channel
                channel: Optional[TextChannel] = self.client.get_channel(channel_id)
                
                if not channel:
                    print(f'⚠️  [CYCLE {cycle_count}] Channel not found in cache, trying to fetch...')
                    try:
                        channel = await self.client.fetch_channel(channel_id)
                        print(f'✅ [CYCLE {cycle_count}] Channel fetched successfully: {channel.name}')
                    except Exception as e:
                        print(f'❌ [CYCLE {cycle_count}] Cannot fetch channel {channel_id}: {e}')
                        await asyncio.sleep(check_interval)
                        continue
                else:
                    print(f'✅ [CYCLE {cycle_count}] Channel found in cache: {channel.name}')
                
                # Check each username for new tweets
                for username in self.usernames_to_monitor:
                    print(f'   🔍 [CYCLE {cycle_count}] Checking @{username}...')
                    await self._check_and_post_tweets(username, channel, cycle_count)
                
                print(f'\n✅ [CYCLE {cycle_count}] Cycle complete. Next check in {check_interval} seconds...')
                
            except Exception as e:
                print(f'❌ [CYCLE {cycle_count}] Error in monitoring loop: {e}')
                import traceback
                traceback.print_exc()
            
            await asyncio.sleep(check_interval)
    
    async def _get_user_id(self, username: str, cycle: int) -> Optional[str]:
        """Get user ID from username (cached to save API calls)"""
        # Check cache first
        if username in self.user_ids_cache:
            print(f'   ✅ @{username} - User ID found in cache: {self.user_ids_cache[username]}')
            return self.user_ids_cache[username]
        
        print(f'   🔍 @{username} - Fetching user ID from Twitter API...')
        
        try:
            user = await asyncio.to_thread(self.twitter_api.get_user, username=username)
            
            if user and user.data:
                user_id = user.data['id']
                self.user_ids_cache[username] = user_id
                print(f'   ✅ @{username} - User ID obtained and cached: {user_id}')
                return user_id
            else:
                print(f'   ❌ @{username} - No user data returned from API')
                return None
                
        except tweepy.TweepyException as e:
            error_str = str(e)
            print(f'   ❌ @{username} - TweepyException: {error_str}')
            if '429' in error_str or 'rate limit' in error_str.lower():
                print(f'   🚫 @{username} - RATE LIMITED! HTTP 429')
                print(f'   ℹ️  El token de Twitter puede estar incompleto o expirado')
                return None
            else:
                print(f'   ❌ @{username} - Twitter API error')
                return None
        except Exception as e:
            print(f'   ❌ @{username} - Unexpected error: {type(e).__name__}: {e}')
            return None
    
    async def _check_and_post_tweets(self, username: str, channel: TextChannel, cycle: int) -> None:
        """Check for new tweets and post them to Discord"""
        print(f'   📡 [CYCLE {cycle}] Checking for tweets from @{username}...')
        
        try:
            # Step 1: Get user ID
            user_id = await self._get_user_id(username, cycle)
            if not user_id:
                print(f'   ⏭️  [CYCLE {cycle}] @{username} - Skipping due to missing user ID')
                return
            
            # Step 2: Get since_id (last tweet we've seen)
            since_id = self.last_tweet_ids.get(username)
            if since_id:
                print(f'   📍 [CYCLE {cycle}] @{username} - Will fetch tweets AFTER ID: {since_id}')
            else:
                print(f'   📍 [CYCLE {cycle}] @{username} - First check, will initialize with latest tweet')
            
            # Step 3: Fetch tweets from Twitter API
            print(f'   🌐 [CYCLE {cycle}] @{username} - Making API call to get_users_tweets...')
            params = {
                'max_results': 10,
                'tweet_fields': ['created_at', 'public_metrics'],
            }
            
            if since_id:
                params['since_id'] = since_id
            
            try:
                tweets_response = await asyncio.to_thread(
                    self.twitter_api.get_users_tweets, 
                    user_id, 
                    **params
                )
                print(f'   ✅ [CYCLE {cycle}] @{username} - API call successful')
            except tweepy.TweepyException as e:
                error_str = str(e)
                print(f'   ❌ [CYCLE {cycle}] @{username} - TweepyException during API call: {error_str}')
                if '429' in error_str or 'rate limit' in error_str.lower():
                    print(f'   🚫 [CYCLE {cycle}] @{username} - RATE LIMITED! HTTP 429')
                    print(f'   ⏰ [CYCLE {cycle}] @{username} - Próximo intento en {self.check_interval}s')
                    print(f'   ℹ️  Posibles causas:')
                    print(f'       - Bearer Token incompleto o expirado')
                    print(f'       - Demasiadas solicitudes simultáneas')
                    print(f'       - Límite de plan free de Twitter alcanzado')
                return
            except Exception as e:
                print(f'   ❌ [CYCLE {cycle}] @{username} - Unexpected error during API call: {type(e).__name__}: {e}')
                return
            
            # Step 4: Check if we have tweets
            if not tweets_response or not tweets_response.data:
                print(f'   📭 [CYCLE {cycle}] @{username} - No new tweets found')
                return
            
            print(f'   📬 [CYCLE {cycle}] @{username} - Found {len(tweets_response.data)} new tweets')
            
            # Step 5: Process each tweet
            for idx, tweet in enumerate(reversed(tweets_response.data), 1):
                tweet_id = tweet['id']
                tweet_text = tweet['text']
                created_at = tweet.get('created_at', 'Unknown')
                
                print(f'   📝 [CYCLE {cycle}] @{username} - Tweet {idx}/{len(tweets_response.data)}')
                print(f'      ID: {tweet_id}')
                print(f'      Created: {created_at}')
                print(f'      Text: {tweet_text[:80]}...')
                
                # Check for spoiler filter
                if '#spoilersie' in tweet_text.lower():
                    print(f'   ⏭️  [CYCLE {cycle}] @{username} - SKIPPING (contains #spoilersie)')
                    self.last_tweet_ids[username] = tweet_id
                    continue
                
                # Update last seen tweet ID
                self.last_tweet_ids[username] = tweet_id
                
                # Post to Discord
                try:
                    tweet_url = f'https://twitter.com/{username}/status/{tweet_id}'
                    
                    embed = Embed(
                        description=tweet_text,
                        color=Color.blue(),
                        url=tweet_url
                    )
                    embed.set_author(
                        name=f'@{username}',
                        url=f'https://twitter.com/{username}',
                        icon_url='https://abs.twimg.com/icons/apple-touch-icon-192x192.png'
                    )
                    embed.add_field(
                        name='🔗 Ver en Twitter',
                        value=f'[Haz clic aquí para ver el tweet]({tweet_url})',
                        inline=False
                    )
                    embed.set_footer(
                        text=f'Twitter • {created_at}',
                        icon_url='https://abs.twimg.com/icons/apple-touch-icon-192x192.png'
                    )
                    
                    await channel.send(embed=embed)
                    print(f'   ✅ [CYCLE {cycle}] @{username} - Tweet posted to Discord!')
                    
                except Exception as e:
                    print(f'   ❌ [CYCLE {cycle}] @{username} - Error posting to Discord: {e}')
        
        except Exception as e:
            print(f'   ❌ [CYCLE {cycle}] @{username} - Unexpected error: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()


async def start_twitter_monitoring(client: Client) -> None:
    """Start the Twitter monitoring task"""
    print('\n' + '='*60)
    print('[START] Initializing Twitter monitoring...')
    print('='*60)
    
    check_interval_str: str = os.getenv('TWITTER_CHECK_INTERVAL', '3600').strip()
    try:
        check_interval: int = int(check_interval_str)
        print(f'✅ [START] Check interval: {check_interval} seconds')
    except ValueError:
        check_interval = 3600
        print(f'⚠️  [START] Invalid TWITTER_CHECK_INTERVAL, defaulting to 3600 seconds')
    
    monitor = TwitterMonitor(client, check_interval=check_interval)
    print(f'✅ [START] TwitterMonitor instance created')
    print(f'✅ [START] Starting monitor_twitter() async task...\n')
    
    await monitor.monitor_twitter()
