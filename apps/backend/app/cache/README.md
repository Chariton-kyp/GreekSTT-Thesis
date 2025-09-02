# Redis Transcription Caching

## Overview

Το Redis caching system επιταχύνει την ανάκτηση ολοκληρωμένων transcriptions αποθηκεύοντάς τα στη μνήμη Redis για 30 λεπτά.

## How it Works

### 1. **Automatic Caching**
- Όταν ολοκληρώνεται μια μεταγραφή, αποθηκεύεται αυτόματα στο Redis
- TTL: 30 λεπτά (1800 δευτερόλεπτα)
- Prefix: `greekstt:transcription:{user_id}:{transcription_id}`

### 2. **Fast Retrieval**
- Κάθε `get_transcription()` ελέγχει πρώτα το Redis cache
- **Cache HIT**: Άμεση επιστροφή από Redis (πολύ γρήγορα)
- **Cache MISS**: Ανάκτηση από database + caching για το μέλλον

### 3. **Automatic Invalidation**
- Όταν ενημερώνεται ένα transcription → cache invalidation + re-caching
- Όταν διαγράφεται ένα transcription → cache invalidation

## Performance Benefits

### Before Redis Caching:
```
Database Query → ~50-200ms
Load Segments → ~10-50ms
Total: ~60-250ms
```

### After Redis Caching:
```
Cache HIT → ~1-5ms
Cache MISS → Same as before, but cached for future
```

**Speed improvement: 10x-50x faster για cached data!**

## Usage in Code

### Automatic Usage (No Code Changes Needed)
```python
# Στο TranscriptionService
transcription = self.get_transcription(123, user_id)
# Αυτόματα ελέγχει Redis πρώτα!
```

### Manual Cache Operations
```python
from app.cache import get_transcription_cache

cache = get_transcription_cache()

# Manual caching
cache.cache_transcription(transcription)

# Manual invalidation
cache.invalidate_transcription(transcription_id, user_id)

# Stats
stats = cache.get_cache_stats()
```

## API Endpoints

### Cache Statistics
```bash
GET /api/cache/stats
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "status": "connected",
    "redis_version": "7.0.0",
    "used_memory_human": "2.5M",
    "cached_transcriptions": 15,
    "cache_prefix": "greekstt:transcription:",
    "default_ttl": 1800
  }
}
```

### Invalidate User Cache
```bash
POST /api/cache/invalidate/user
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Invalidated 5 cached transcriptions",
  "deleted_count": 5
}
```

### Invalidate Specific Transcription
```bash
DELETE /api/cache/invalidate/{transcription_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Cache invalidated for transcription 123"
}
```

### Extend Cache TTL
```bash
POST /api/cache/extend-ttl/{transcription_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "TTL extended for transcription 123"
}
```

## Configuration

### Environment Variables
```bash
# Redis connection (in .env)
REDIS_URL=redis://localhost:6379/0
```

### Cache Settings
```python
# In extensions.py
cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 1800,  # 30 minutes
    'CACHE_KEY_PREFIX': 'greekstt:'
})
```

## Monitoring & Debugging

### Check Cache Status
```bash
# Via API
curl -H "Authorization: Bearer <token>" http://localhost:5001/api/cache/stats

# Via Redis CLI
docker exec -it greekstt_redis redis-cli
> keys greekstt:transcription:*
> ttl greekstt:transcription:1:123
```

### Logs
```python
# Cache HIT
INFO: Retrieved transcription 123 from Redis cache

# Cache MISS  
DEBUG: Fetching transcription 123 from database
DEBUG: Cached transcription 123 after database retrieval
```

## Error Handling

- **Redis Unavailable**: Αυτόματα fallback στη database
- **Cache Corruption**: Safe deserialization με error handling
- **TTL Expiry**: Automatic re-caching όταν ανακτάται από database

## Best Practices

1. **Δεν χρειάζονται αλλαγές στον existing κώδικα** - το caching είναι transparent
2. **Monitor Redis memory usage** - περιορισμένο σε 128MB με LRU eviction
3. **Cache μόνο completed transcriptions** - pending/processing δεν cache-άρονται
4. **Automatic cleanup** - TTL διασφαλίζει ότι το cache δεν γεμίζει

## Testing

```bash
# Start services
cd GreekSTT-Thesis
npm run docker:up

# Create a transcription and check cache
# 1. Upload audio file
# 2. Wait for completion  
# 3. Check /api/cache/stats
# 4. Get same transcription again (should be from cache)
```

## Fallback Strategy

Το σύστημα είναι **fault-tolerant**:
- Αν το Redis πέσει → συνεχίζει να δουλεύει με database
- Αν το cache χαλάσει → automatic invalidation & re-cache
- Αν το network έχει πρόβλημα → graceful fallback