Two years ago I spent about four months building a feature that, as far as I can tell, was used by eleven people. Not eleven thousand. Eleven.

It was a custom report builder for our analytics product. Customers had asked for it on almost every call. "I wish I could just build my own report." We heard it so often it became a running joke in standup. So we built it. Drag and drop fields, saved templates, scheduled exports, the whole thing. The engineering was genuinely good. We were proud of it.

We launched with a blog post and an in-app announcement. Usage spiked for two days while people poked at it, then flattened to almost nothing.

Here is what I got wrong, and I still think about it a lot.

When customers said "I wish I could build my own report," I heard a feature request. What they were actually telling me was that our default reports did not answer their question. Nobody wants to build a report. Building a report is work. They wanted the answer, and they were describing the only path to it they could picture, which was doing it themselves.

If I had asked one more question on any of those calls, something like "what would you put in that report," I would have heard the same three things again and again. Revenue by region with a date comparison. Churn by plan tier. Time to first value by signup source. Three fixed reports. Maybe two weeks of work. Instead I built a general-purpose tool so people could do the work I should have done for them.

The lesson sounds obvious written down, but it was not obvious to me then. A request is a symptom. The customer is telling you where it hurts, not what the treatment should be. They are experts in their problem and amateurs in your product, and if you let them design the solution you end up with something that looks like their workaround rather than an actual fix.

Now when someone asks for a feature, I ask what they would do with it the first time they used it. Then I ask what they would do the second time. Usually the second answer matches the first, and that tells me the flexible version is not what they need. They need one good thing, done for them, that they never have to think about again.

The feature is still in the product. We never removed it. Every few months someone new discovers it and sends a kind message, and I am glad it exists for them. But I stopped counting it as a win a long time ago. I count it as the most expensive lesson I have taken in this job, and one I am still grateful for.