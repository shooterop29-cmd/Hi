# MultiSaver Pro Bot — Railway deployment

## Files
- `main.py`: bot application
- `Dockerfile`: installs FFmpeg (needed to merge separate audio/video streams)
- `requirements.txt`: Python dependencies

## Railway setup
1. Upload these files to your GitHub repository and deploy the repository on Railway.
2. In Railway → Variables, add:
   - `BOT_TOKEN` = the current token from @BotFather
   - `ADMIN_ID` = your Telegram numeric user ID (optional; defaults to the ID in the script)
3. Make sure only **one running Railway replica/service** uses this bot token.
4. Redeploy and check the deployment logs.

## Important error explanations
- `ffmpeg is not installed`: fixed by the Dockerfile. Make sure Railway is actually building with this Dockerfile.
- `Conflict: terminated by other getUpdates request`: another process/service is polling with the same bot token. Stop the old deployment or any local copy; keep one poller only.
- `InvalidToken: ... rejected by the server`: the `BOT_TOKEN` Railway variable is wrong, expired, or has extra characters. Create/revoke a token with @BotFather and update the variable. Never paste the token into chat or commit it to GitHub.
- Instagram `No video formats found`, `Media number out of range`, or content unavailable: this is not necessarily a Python bug. Update/redeploy yt-dlp (this requirements file installs the current release at build time). Some posts are private, region-restricted, login-gated, deleted, or image-only. For login-gated posts, optionally set `INSTAGRAM_COOKIES` to the Netscape-format cookies exported from an account that is allowed to view the post. Keep cookies private and rotate them if exposed.

## Notes
- Telegram's hosted Bot API has a per-file upload limit; this bot uses 49 MB as a conservative default. Set `MAX_UPLOAD_MB` if your deployment uses a different Bot API setup.
- User language preferences and `/stats` counts are in memory and reset after a restart. Add a database for persistence before relying on them.
- Download only content you have permission to download and share.
