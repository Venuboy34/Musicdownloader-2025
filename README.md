# Telegram Music Bot Deployment Guide for Koyeb

## 1. Prepare Your Bot Files

Make sure you have the following files:
- `bot.py` - Your main bot code
- `requirements.txt` - Dependencies for your bot
- `Dockerfile` - Instructions for building your container
- `welcome.jpg` - Welcome image for your bot

## 2. Create a Telegram Bot

1. Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Use the `/newbot` command to create a new bot
3. Follow the instructions and note down the API token provided

## 3. Set Up Koyeb Account

1. Go to [koyeb.com](https://koyeb.com) and sign up for a free account
2. Verify your email and log in to your Koyeb dashboard

## 4. Deploy on Koyeb

### Option 1: Deploy using GitHub repository

1. Push your bot code to a GitHub repository
2. In Koyeb dashboard, click "Create App"
3. Select "GitHub" as the deployment method
4. Connect your GitHub account and select your repository
5. Configure your app:
   - Name: `telegram-music-bot` (or any name you prefer)
   - Region: Choose the closest to your users
   - Instance Type: Select "Free tier"
   - Environment Variables: Add `TELEGRAM_BOT_TOKEN` with your bot token
6. Click "Deploy"

### Option 2: Deploy using Docker

1. Install Docker on your local machine
2. Build the Docker image:
   ```
   docker build -t telegram-music-bot .
   ```
3. Create a free account on Docker Hub
4. Tag and push your image:
   ```
   docker tag telegram-music-bot yourusername/telegram-music-bot:latest
   docker push yourusername/telegram-music-bot:latest
   ```
5. In Koyeb dashboard, click "Create App"
6. Select "Docker" as the deployment method
7. Enter your Docker image URL: `yourusername/telegram-music-bot:latest`
8. Configure your app:
   - Name: `telegram-music-bot` (or any name you prefer)
   - Region: Choose the closest to your users
   - Instance Type: Select "Free tier"
   - Environment Variables: Add `TELEGRAM_BOT_TOKEN` with your bot token
9. Click "Deploy"

## 5. Test Your Bot

1. Once deployment is complete, find your bot on Telegram
2. Start a conversation with your bot by sending `/start`
3. You should see the welcome image and message
4. Try searching for a song to test the download functionality

## Notes

- Koyeb's free tier provides limited resources but is sufficient for a basic bot with moderate usage
- The bot will run 24/7 as long as your Koyeb account remains active
- Monitor your usage to ensure you stay within the free tier limits

## Troubleshooting

- If your bot doesn't respond, check the logs in the Koyeb dashboard
- Ensure your `TELEGRAM_BOT_TOKEN` environment variable is correctly set
- Verify that your bot has permission to send messages, photos, and audio files
