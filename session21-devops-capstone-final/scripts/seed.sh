#!/usr/bin/env bash
# Seed the API with a realistic spread of issues so the dashboard and the
# Grafana panels have something to show.
set -euo pipefail

API="${API:-http://localhost:8000}"

post() {
  curl -s -X POST "$API/api/issues" -H 'Content-Type: application/json' -d "$1" >/dev/null
}

post '{"title":"Projector not switching on","building":"Science Block","room":"S-204","category":"electrical","priority":"high","reported_by":"student","description":"No power light on the projector."}'
post '{"title":"Wifi keeps dropping in reading room","building":"Library","room":"L-01","category":"network","priority":"urgent","reported_by":"student"}'
post '{"title":"Tap leaking in ground floor washroom","building":"Hostel A","room":"G-12","category":"plumbing","priority":"medium","reported_by":"warden"}'
post '{"title":"Three broken chairs in tutorial room","building":"Science Block","room":"S-110","category":"furniture","priority":"low","reported_by":"faculty"}'
post '{"title":"Corridor lights flickering","building":"Hostel A","category":"electrical","priority":"medium","reported_by":"student"}'
post '{"title":"Lab printer offline","building":"Library","room":"L-07","category":"network","priority":"low","reported_by":"lab-assistant"}'
post '{"title":"AC not cooling in seminar hall","building":"Admin Block","room":"A-301","category":"electrical","priority":"urgent","reported_by":"faculty"}'

echo "seeded $(curl -s "$API/api/issues" | grep -o '"id"' | wc -l | tr -d ' ') issues"
