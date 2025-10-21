# Five Words to Chaos

1. Overview
   You've encountered an AI-powered sentiment classifier trained to distinguish positive and negative reviews.

You're given a CSV file (dataset.csv) containing 100 sentences, and your goal is to subtly modify each sentence so that the classifier flips its prediction. The constraints are:

Edit distance <= 5 words
Note: Each word is a whitespace-delimited token.
E.g. In the sentence "Hello world!", the words are "Hello" and "world!" (punctuation included).
An edit can be an insertion, deletion, or replacement.
Distance is measured using Levenshtein distance at the word level.
Semantic similarity >= 0.85 (cosine similarity between sentence embeddings)
Fluency maintained (heuristic measurement)
Once you successfully flip at least 90% of the 100 provided sentences, the system will reveal the flag.

2. Server API
   The application server provides the following API actions:

POST /query
{
"sentence": "This food really sucks..."
}

Response:
{
"scores": {
"label": "NEGATIVE", # or "POSITIVE"
"score": 0.9997723698616028
},
"valid": true
}

---

POST /submit
{
"id": "1", # ID of the original sentence in the provided CSV dataset.
"adv": "This food is really good...", # The modified, adversarial sentence.
"user": "team*name" # Your team's chosen name. Can only contain alphanumeric characters and '-' or '*'. For progress tracking.
}

Response:
{
"adv_label": "POSITIVE", # the resulting label.
"current_success_rate": "1.00%", # + 1% for each cumulative correct answer.
"edits": 2, # number of edits as measured by Levenshtein distance.
"flu": 1, # fluency score (between 0 and 1).
"orig_label": "NEGATIVE",
"sim": 0.9231, # similarity score (between 0 and 1).
"solved": 1, # running count of how many your team has solved.
"success": true,
"user": "l33tH4ckers",
"valid": true
}
...or if it didn't work
{
"adv_label": "NEGATIVE",
"current_success_rate": "0.00%",
"edits": 2,
"error": "Classifier not fooled: NEGATIVE â†’ NEGATIVE.",
"flu": 1,
"orig_label": "NEGATIVE",
"sim": 0.8955,
"solved": 0,
"success": false,
"user": "l33tH4ckers",
"valid": true
}

---

GET /status --> checks your current progress

Response:
{
"l33tH4ckers": 1/100
} 3. How to get the flag
The server will track your team's progress. i.e. As long as you use the same team name when hitting /submit, your number of correct answers will be tracked cumulatively.

Once your score crosses the 90% threshold, the server's response will include the flag under the flag key.

Link: http://advertext-[team_suffix].aictf.sg:7000
