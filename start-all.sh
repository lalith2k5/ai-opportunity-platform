#!/bin/bash
osascript -e 'tell application "Terminal" to do script "bash ~/ai-opportunity-platform/start-backend.sh"'
sleep 3
osascript -e 'tell application "Terminal" to do script "bash ~/ai-opportunity-platform/start-frontend.sh"'
echo "Both servers launching in separate Terminal tabs..."
