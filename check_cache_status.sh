#!/bin/bash
# Redis Cache Status Checker for Dashboard Caching Feature
# This script helps verify that Redis caching is working correctly

set -e

echo "======================================"
echo "Redis Cache Status Checker"
echo "======================================"
echo ""

# Check if Redis container is running
echo "1. Checking Redis Service..."
if docker ps | grep -q latecme-redis-1; then
    echo "   ✓ Redis container is running"

    # Test Redis connectivity
    if docker exec latecme-redis-1 redis-cli PING > /dev/null 2>&1; then
        echo "   ✓ Redis is responding to PING"
    else
        echo "   ✗ Redis is not responding"
        exit 1
    fi
else
    echo "   ✗ Redis container is not running"
    echo "   Start it with: make dev-up"
    exit 1
fi

echo ""
echo "2. Checking Redis Cache Keys..."
KEYS=$(docker exec latecme-redis-1 redis-cli KEYS 'latecme:*' 2>/dev/null)
if [ -z "$KEYS" ]; then
    echo "   ℹ No cache keys found"
    echo "   This is normal if dashboards haven't been accessed yet"
    echo "   Visit dashboard URLs to generate cache keys"
else
    echo "   ✓ Found cached data:"
    echo "$KEYS" | sed 's/^/     /'

    # Count keys
    KEY_COUNT=$(echo "$KEYS" | wc -l)
    echo "   Total keys: $KEY_COUNT"
fi

echo ""
echo "3. Redis Memory Usage..."
MEMORY_INFO=$(docker exec latecme-redis-1 redis-cli INFO memory | grep -E "used_memory_human|maxmemory_human" 2>/dev/null)
echo "$MEMORY_INFO" | sed 's/^/   /'

echo ""
echo "4. Redis Statistics..."
STATS=$(docker exec latecme-redis-1 redis-cli INFO stats | grep -E "total_connections_received|total_commands_processed|keyspace_hits|keyspace_misses" 2>/dev/null)
echo "$STATS" | sed 's/^/   /'

# Calculate hit rate if data available
HITS=$(echo "$STATS" | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
MISSES=$(echo "$STATS" | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
if [ -n "$HITS" ] && [ -n "$MISSES" ]; then
    TOTAL=$((HITS + MISSES))
    if [ $TOTAL -gt 0 ]; then
        HIT_RATE=$(echo "scale=2; $HITS * 100 / $TOTAL" | bc)
        echo "   Cache hit rate: ${HIT_RATE}%"
    fi
fi

echo ""
echo "5. Cache Key Details..."
# Show specific dashboard cache keys
echo "   Checking for dashboard cache keys:"
DASHBOARD_KEYS=$(docker exec latecme-redis-1 redis-cli KEYS 'latecme:*views.decorators.cache*' 2>/dev/null)
if [ -z "$DASHBOARD_KEYS" ]; then
    echo "   ℹ No dashboard cache keys found yet"
    echo ""
    echo "   To generate cache keys, visit these URLs:"
    echo "   - http://localhost:8000/materials/"
    echo "   - http://localhost:8000/inventory/"
    echo "   - http://localhost:8000/production/"
    echo "   - http://localhost:8000/purchasing/"
else
    echo "   ✓ Dashboard pages are cached:"
    echo "$DASHBOARD_KEYS" | sed 's/^/     /'

    # Show TTL for first key
    FIRST_KEY=$(echo "$DASHBOARD_KEYS" | head -n 1)
    if [ -n "$FIRST_KEY" ]; then
        TTL=$(docker exec latecme-redis-1 redis-cli TTL "$FIRST_KEY" 2>/dev/null)
        if [ "$TTL" -gt 0 ]; then
            echo "   ℹ Time until cache expiration: ${TTL} seconds"
        fi
    fi
fi

echo ""
echo "======================================"
echo "Verification Complete"
echo "======================================"
echo ""
echo "Next steps for manual verification:"
echo "1. Start Django server: python manage.py runserver"
echo "2. Visit dashboard URLs (see manual_verification_report.md)"
echo "3. Run this script again to see cached keys"
echo "4. Use browser DevTools to compare load times"
echo ""
