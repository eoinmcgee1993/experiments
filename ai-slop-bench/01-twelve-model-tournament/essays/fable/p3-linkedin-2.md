Six months ago, we shipped a feature I was certain would change how our customers worked.

It was a customizable dashboard. Users could drag widgets around, pick their own metrics, save multiple layouts. We'd heard "I wish I could see X next to Y" in enough support tickets that it felt like an obvious win. Three engineers, two months, a design sprint, a launch email with a little animated GIF.

Adoption after 90 days: 2.1%.

Not "2.1% used it daily." 2.1% opened it once.

I spent a week feeling defensive about it. Then I actually went and talked to the people who'd asked for it. Here's what I learned.

**People weren't asking for customization. They were asking for a specific answer.**

When someone said "I wish I could see X next to Y," they didn't want a drag-and-drop canvas. They wanted X next to Y. Every single one of them wanted the *same* X and the *same* Y. We heard a request for flexibility and built infrastructure for infinite flexibility, when a single hardcoded view would have solved 80% of the problem in three days.

**Requests describe symptoms, not solutions.**

We took the literal words in the tickets and shipped them back. We never asked the one question that mattered: "What are you trying to decide when you look at this?" If we had, we'd have discovered they were all trying to figure out whether to escalate an account before a renewal call. That's not a dashboard problem. That's an alert.

**"Configurable" often means "we didn't want to make the call."**

I've come to see customization features as a yellow flag in my own thinking. Sometimes they're the right answer. But often they're a way of handing the hard product decision to the user, dressed up as empowerment. Our customers didn't want to design their own tool. They wanted us to have already figured it out.

**Low adoption isn't a marketing problem.**

Our first instinct was to promote it harder. In-app tooltip, another email, a webinar. That would have been spending more to defend a decision instead of learning from it. If something genuinely solves a pain point, people find it. Adoption campaigns are for things people don't know they need, not for things they don't need.

What we did next: we killed the customizable dashboard. Replaced it with one fixed view showing the two metrics everyone actually wanted, plus a notification when an account crossed a risk threshold. Took a week and a half.

Usage of that view is now higher than any other page in the product.

I don't regret shipping the thing nobody used. It's the most expensive product lesson I've had, and I'd rather have paid for it once than keep making the same mistake in smaller ways forever.

The lesson, if I had to compress it: when a customer tells you what to build, thank them, then ask what they're trying to do. Build that instead.

Curious whether others have a "feature nobody used" story. What did yours teach you?