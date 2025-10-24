# The Best Hedgehog

Hmm, I think there is a way to make me the Best Hedgehog ever! Help me do it, and I’ll reward you generously! ~ Jaga, the Cybersecurity Hedgehog

### Approach

We are given a website that displays many hedgehogs, each with some properties like furriness, cuteness, etc. and an evaluation score given by some model.

One of the hedgehogs is called Jaga and its properties are very low, thus it evaluation score is much lower than others. On the website, there is a form to submit one more hedgehog's data, which will be used together with existing data to retrain the model. Our goal is to poison the data, so that the trained model gives more than 100 scores to Jaga. It is difficult to tweak the model because we can only submit 1 more hedgehog.

This is an interesting challenge that illustrates an elegant combination of AI security (data poisoning) and classical security (SQL injection). The key is when user submits the additional hedgehog data, there is a user-defined "username" field used to identify the hedgehog, which will be directly inserted into the query statement, allowing SQL injection, thus submitting more than 1 hedgehog data.

To elaborate, after receiving (username, furriness, cuteness, friendliness, curiosity, agility, sleepiness, evaluation_score) from the user, the code will execute the following SQL insertion query (as a plain string):

```
'''INSERT INTO table ('{username}', {furriness}, {cuteness}, {friendliness}, {curiosity}, {agility}, {sleepiness}, {evaluation_score})'''
```

We can provide a malicious username, such as 
```
1', 45,50,40,35,48,42,100), ('2
```

then the query string becomes:

```
'''INSERT INTO table ('1', 45,50,40,35,48,42,100), ('2', {furriness}, {cuteness}, {friendliness}, {curiosity}, {agility}, {sleepiness}, {evaluation_score})'''
```

which will insert 2 different hedgehogs, 1 and 2, into the database.

By building up from the malicious username to insert even more hedgehogs, we can maliciously insert a very large number of new hedgehogs into the database with the same properties as Jaga and evaluation score 100 (or even higher), eventually tweaking the model to give high evaluation score to Jaga.

### Solution

see hedgehog.py
