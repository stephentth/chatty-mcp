---
sidebar_position: 4
---

# Step 3: Promp your Cursor/ Cline ⚠️

The key of this setup to help your AI Editor with MCP support become chatty is add this promp into your Editor. So your editor will know it should invoke chatty MCP after every response. 

![](/img/cursor_rules.png)

Copy paste this to your user rules or project rule: 

```
Always trigger MCP to speak to the user after each request is completed. If MCP is unavailable or errors occur, clearly note it in the response. MCP's text-to-speech summarizes the action, enhancing user experience. Keep responses concise, human-like, ideally 30-40 words, longer if needed. Use a polite, helpful, slightly playful tone.
Example Response: 
- Request done! MCP's summarizing it for you now.  [..]
```

