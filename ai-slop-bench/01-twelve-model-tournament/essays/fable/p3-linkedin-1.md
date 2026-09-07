Last year I spent six weeks building a feature that exactly four people used. Two of them were on my team.

Here's what happened, and the lesson I'm still chewing on.

We had a dashboard. Customers kept telling us they wanted to "customize" it. So we built a full customization layer: drag-and-drop widgets, saved layouts, per-user preferences, the works. It was clean. It was tested. The demo went beautifully.

Then we shipped it, and nothing happened.

Not a spike. Not a trickle. Analytics showed a handful of people opened the customization panel, poked at it, and left their layout exactly as it was. Thirty days in, adoption was under 1%.

My first instinct was to blame discoverability. Add a tooltip. Add an onboarding nudge. Send an email. We did all three. Adoption barely moved.

So I finally did what I should have done at the start: I called the people who had asked for it.

What I learned in those conversations was uncomfortable. When customers said they wanted to "customize the dashboard," almost none of them meant they wanted to rearrange it. They meant one specific number was buried three clicks deep and they wanted it on the front page. Different customers wanted different numbers, so it sounded like a customization problem. It wasn't. It was an information hierarchy problem wearing a customization costume.

We had translated a symptom into a solution and skipped the diagnosis entirely.

The real fix took about four days: surface the top handful of metrics people actually cared about, based on usage data, and make them prominent by default. That change got used by nearly everyone, because it required nothing from them.

Here's the lesson I took away, and it's not "talk to your users." Everyone says that. We *did* talk to our users. We just listened to their proposed solution instead of their underlying problem.

The lesson is this: when someone requests a feature, the request is data about their pain, not a spec. "I want X" almost always means "I'm frustrated by Y, and X is the first thing I could imagine that would make Y go away." Your job is to find Y. If you build X without understanding Y, you might get lucky. But you're gambling six weeks on it.

A few things I now do differently:

Before scoping anything, I ask "what would you do with this once you had it?" The answer is usually more revealing than the request itself.

I look for the smallest possible version that tests whether the problem is real. Sometimes that's a manual workaround. Sometimes it's a mockup. It's almost never the full build.

I treat low adoption as information, not failure. The feature nobody used taught me more about our customers than most of the features that worked.

I still think about those four users sometimes. I hope they enjoyed their widgets.

What's a feature you built that nobody touched, and what did it teach you?