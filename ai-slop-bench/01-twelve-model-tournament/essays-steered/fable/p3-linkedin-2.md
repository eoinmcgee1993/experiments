Two years ago I spent about four months building a feature that, as far as I can tell, was used by nine people. Not nine thousand. Nine. And I think three of them were on my team testing it.

The feature was a customizable dashboard. Users could drag widgets around, pick which metrics showed up, save different layouts for different days. We had heard from a handful of customers that our default view didn't fit their workflow, and I took that and ran with it. I wrote a spec. I got design involved. We built a whole layout engine. I remember demoing it to the sales team and feeling genuinely proud of how smooth the drag and drop felt.

Then we shipped it, and nothing happened. No spike in engagement. No support tickets, good or bad. A few people opened the customization panel, moved one widget, and never came back to it.

For a while I told myself it was a discoverability problem. We added a tooltip. We added a banner. We put it in the release notes twice. Nothing changed.

What finally made it click was a call with one of the customers who had originally asked for it. I asked her why she hadn't set up her own layout. She said, and I'm paraphrasing only slightly, "I don't want to design a dashboard. I want you to know what I need to see." She had never wanted flexibility. She wanted us to be right about the default. Flexibility was what she asked for because it was the easiest thing to say when the default was wrong.

That's the lesson I keep coming back to. When someone asks for a feature, they are usually describing a solution they can imagine, not the problem they actually have. My job was to dig underneath the request, and instead I took it at face value because it was concrete and buildable and I could picture the demo.

The honest version of the story is that I was also a little bored. The default view was a hard, unglamorous problem that required looking at a lot of data and talking to a lot of people and probably ending up somewhere unsatisfying. A layout engine was fun. I could see progress every day. I let that pull me.

What I do differently now is pretty simple. Before I write a spec, I try to say the problem out loud without mentioning any solution, and I check whether the customer nods. If I can't do that, I'm not ready to build. And when a request comes in as a fully formed feature, I treat that as a signal that I haven't asked enough questions yet, not as a shortcut.

We eventually rebuilt the default view based on what people actually looked at first every morning. It took three weeks. Engagement went up noticeably. Nobody asked for customization again.

I still think about those nine users sometimes. I hope the drag and drop was nice for them.