**We spent four months building a feature. Six people used it.**

Not six percent. Six people. Out of about 4,000 weekly active accounts.

The feature was a custom dashboard builder. Drag your own widgets, pick your own metrics, save your own views. It came up in nearly every enterprise sales call. It was the third-most-requested item in our feedback tool. Three engineers and a designer worked on it for a full quarter.

We shipped it on a Thursday. I posted about it in the company Slack with a rocket emoji.

By the following month, adoption had flatlined at 0.4%. Retention among the people who *did* build a dashboard was worse than average — they'd build one, never open it again, and go back to the default view.

Here's what I got wrong, and it wasn't a prioritization problem. It was a listening problem.

Customers weren't asking for a dashboard builder. They were telling me they didn't trust our numbers.

When someone said "I want to build my own view," what they meant was: "Your default report shows a number my CFO doesn't recognize, and I can't figure out how you calculated it, so I export to a spreadsheet and rebuild it myself." The request was a workaround they'd invented for a problem they didn't have the language for. I took the workaround at face value and built it faster and prettier.

The fix, when we finally found it, was a definitions panel. Click any metric, see exactly how it's computed, which filters apply, and what's excluded. Two engineers, three weeks. Spreadsheet exports dropped 60%. Nobody ever asked us for a definitions panel.

Three things I do differently now:

**I ask about the last time, not the next time.** "Would you use this?" gets you politeness. "Walk me through the last time you needed this — what did you actually do?" gets you the truth, including the ugly workaround that reveals the real problem.

**I write down what would make us wrong.** Before we build, we agree on a number: if fewer than X% of eligible accounts use this in 30 days, we were wrong about the problem, and we run a retro instead of a victory lap. Having that number in writing beforehand makes it much harder to quietly redefine success afterward.

**I separate demand from evidence.** A feature request is a signal that something hurts. It is not a diagnosis. Ten people asking for the same thing can still be ten people describing the same symptom of an entirely different disease.

The uncomfortable part: I don't think we were sloppy. We talked to customers. We looked at the data. We just mistook *volume of requests* for *understanding of the problem*, and those are not the same thing at all.

What's the feature you're proudest of killing?