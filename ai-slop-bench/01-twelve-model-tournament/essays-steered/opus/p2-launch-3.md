Starting today, you can connect your helpdesk to Slack and have a daily summary of your open tickets posted to any channel you choose.

This one came directly from you. Over the past year, the request we heard most often was some version of "I don't want to log in every morning just to see what's waiting." Support leads told us they were manually copying ticket counts into standups. A few of you built your own scripts against our API to do roughly this, which we took as a strong hint.

Here's how it works. In your account settings, under Integrations, you'll find a new Slack card. Click connect, authorize the app, and pick the channel where you want the summary to land. That's the whole setup, and it takes about a minute.

Once connected, we'll post a message every weekday morning with a snapshot of where things stand: how many tickets are open, how many are unassigned, how many have breached your first response target, and which ones have been sitting longest without a reply. Each ticket in the summary links straight back to the conversation, so anyone in the channel can jump in and pick something up.

You can set the delivery time to match when your team actually starts work, and you can choose which days it posts. If your support team runs weekends, turn Saturday and Sunday on. If Monday morning is when your queue matters most, you can leave it at that. You can also filter the summary by team, product area, or any tag you already use, which means a channel for billing questions and a separate one for technical escalations, each seeing only what's relevant to them. There's no limit on how many summaries you configure.

A note on permissions, since a few beta customers asked. The integration respects your existing access rules. If a ticket is restricted to a particular group inside the helpdesk, the summary won't expose its contents to a channel outside that group; it will show as a count only. We'd rather be conservative here, but if that behavior gets in your way, tell us and we'll look at making it configurable.

This is available now on all paid plans at no extra cost. It's also the foundation for a few things we're working on next, including the ability to reply to a ticket directly from Slack and alerts that fire the moment a high priority ticket goes unclaimed for too long. Both are in early testing with a handful of accounts, and we'll open them up more broadly in the next couple of months.

If you'd like to try it, head to Integrations in your settings. The setup guide walks through the Slack permissions in more detail if your workspace requires admin approval, which many do.

And as always, if you use this and something feels off, or you want it to do something it doesn't, reply to this email. The requests that made this feature happen came in exactly that way.