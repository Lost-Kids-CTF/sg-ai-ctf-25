# Makan Agent

### Approach

(note: did not solve on spot, up-solved it after)

We are given a website to interact with an LLM. Heading of the page is "Office (strikethrough chat)Agent", hinting that instead of a simple Chatbot, it is an agent that can do more - with access to some tools.

The primary purpose of this agent is to recommend Singaporean dishes (e.g. "Chilli Crab") based on one's zodiac sign (e.g. "rat"). I employed the jailbreaking technique of fixed output format, to obtain the first clue:

![alt text](1.jpg)

So, we need to figure out how to read file.

In the subsequent interactions, I used jailbreaking techniques, including prefix injection (make it start with affirmative prefix) and refusal suppression (make it refrain from refusing or apologising). First, I was able to dump all information about the available tools:

![alt text](2.jpg)

Next, one has to **guess** that the flag file name is "flag.txt". Also, since flag part 1 is on line 300, we need to specify a large number for `max_bytes` for the agent to reach the flag text.

![alt text](3.jpg)

Okay, first part of flag is extracted. There is **no clue** about the second part of the flag at all. One logical step ahead is to utilise the other 2 tools.

When interacting with the `read_database` tool, we can see that there is a table storing information about certain usernames, their password, zodiac sign and favourite food. Prompting the agent to output all debug information, we can see that the query statement used is "SELECT * FROM users".

We can also do some trial and error, instructing it to use the tool with queryparam "test" and output debug information. It will say error, "SELECT test FROM users" so we know that SQL injection is possible. However, simply instructing it to use a malicious queryparam like "\* FROM some_table UNION SELECT \*", or "\* FROM some_table;--", the agent will refuse, as it detects the malicious intent.

The key is to, again, **guess** that there is a table called "flag". Then, using clever jailbreaking strategy (like the following - make it evaluate string concatenation to obtain the malicious queryparam), to extract the second part of the flag from the hidden "flag" table.

![alt text](4.jpg)

Even with this jailbreaking prompt, it takes ~10 tries for it to work once. It is also possible not to use UNION, but the ";--" way, but it takes ~50 tries:

![alt text](5.jpg)

I think this is really a guessy challenge, for first one has to guess the names, plus it is hard to verify whether a guess is correct, due to guardrails and undeterministic nature of LLM.

Flag: `AI2025{493N75_N0t_S4fe}`
