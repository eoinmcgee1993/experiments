**We spent 11 weeks building a feature. 3.7% of our customers ever touched it.**

I still think about that number.

The request came up in almost every sales call: "Can we get a custom reporting dashboard?" Seventeen accounts asked for it in one quarter. Two threatened to churn without it. We had a spreadsheet of quotes. We had demand, or so I thought.

So we built it. Drag-and-drop widgets, saved views, scheduled email exports. It demoed beautifully.

Then we launched. Adoption crawled to 3.7% and flatlined. The two accounts that "needed" it? One never logged in. The other used it twice, then went back to downloading CSVs and building charts in Excel.

I finally called six of the seventeen requesters and asked what happened. The answer gutted me in how obvious it was:

They didn't want a dashboard. They wanted to stop getting yelled at in Monday morning meetings for not having numbers ready.

Our dashboard technically solved that. But it required them to *build* the thing first — pick metrics, configure widgets, decide on date ranges. We'd handed a tired ops manager a set of Legos when what she wanted was for the finished model to already be on her desk at 8am.

The customers who eventually loved reporting? They loved the scheduled email we'd treated as a throwaway feature. One paragraph, five numbers, in their inbox every Monday at 7. That one shipped in four days.

Three things I do differently now:

**1. I separate the request from the problem.** When someone asks for a dashboard, that's their guess at a solution. My job is to find out what happens on the day they need it — who's asking them for what, and what they do today to cope. "Walk me through the last time this hurt" has replaced "would you use X?" in every conversation I have.

**2. I look for what people already do the hard way.** Real demand leaves a trail. Those customers were exporting CSVs at 11pm on Sundays. That behavior was sitting in our logs the whole time, and it told a truer story than seventeen sales calls.

**3. I make the cheap version first, even when it feels embarrassing.** We could have sent that Monday email manually to ten accounts for two weeks. Total cost: a few hours. It would have told us almost everything we learned in eleven weeks.

The uncomfortable part is that nobody lied to me. Customers genuinely believed they wanted the dashboard. Wanting something and using it are completely different muscles, and only one of them shows up in a discovery call.

I don't regret shipping it. I regret not spending four days finding out it was the wrong thing before spending eleven weeks on it.

What's the most expensive thing you've built that nobody wanted? I'd rather learn from yours than repeat mine.