We spent eleven weeks building a custom report builder. Three months after launch, 1.4 percent of accounts had used it once. About a third of those were people on my own team clicking around to make sure it still worked.

I want to be honest about how confident I was. We had the requests documented. Twenty three customers had asked for "better reporting" in the previous two quarters. Sales brought it up on every pipeline call. I had a spreadsheet. I had quotes. I had, I thought, evidence.

What I actually had was a pile of people describing a solution, and me writing it down as a requirement.

When we finally went back and called fifteen of those customers, the pattern was almost funny. Nobody wanted to build reports. They wanted one number. Usually weekly active users by workspace, occasionally revenue by plan tier, and they wanted it to show up in their inbox on Monday morning so they could paste it into a deck or a Slack channel before their own leadership meeting. The reason they asked for a report builder was that they assumed we would never build the thing they actually needed, so they asked for the general tool that would let them do it themselves.

We replaced eleven weeks of work with a scheduled email digest. It took nine days. Adoption crossed forty percent within a month, and it stayed there, which is the part I care about more.

The lesson I took from it is that I was asking the wrong question in customer conversations. I kept asking versions of "would you use this?" and people are extremely polite, so they said yes. Now I ask what they did the last time they needed this, in detail, including the ugly parts. Did you export a CSV. Did you screenshot the dashboard. Did you ask an engineer to run a query. Did you just guess. The workaround someone has already built with their own time is a much better signal than anything they say about a hypothetical future.

The second lesson, which took me longer to accept, is that a big request is often a small problem wearing a costume. "Better reporting" sounds like a platform investment. It was a cron job and a template. When a request feels large and vague, that is usually a sign I have not found the specific job underneath it yet, and shipping before I find it is just an expensive way to keep looking.

I still think about that report builder. It was well built. The engineers did good work. It had a clean empty state that almost nobody ever saw.

If you have shipped something that nobody used, I would genuinely like to hear what you learned from it. I think we talk about those far less than we should, and they teach more than the launches that go well.