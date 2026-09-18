"""Long-lived Telegram approval listener (optional).

Runs ``telegram_approval.poll_loop()`` so the Approve/Reject buttons on the
Telegram approval messages actually do something. The web console does NOT
need this — approving there writes ``status='queued'`` and the hourly
``FollowerDashboard-PublishApproved`` task publishes it. Use this only if you
also want to approve straight from Telegram.

Run it by hand (it blocks forever):

    python approval_poll.py
"""
import os
import sys

# Resolve imports against this file's own folder, so the script works no matter
# where it is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import telegram_approval

if __name__ == "__main__":
    telegram_approval.poll_loop()
