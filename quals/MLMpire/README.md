# MLMpire

An eager intern at MLMpire handed a log-normalization model more than it should have: raw server logs with passwords left in plain sight. The model still remembers. You've got the weights. Crack its learned memory, follow the breadcrumbs in its predictions, and pull the flag out from where it's been quietly embedded.

### Solution

Using the prompt string "log entry related to the flag: AI2025{", we are able to make the MLM output the flag

```
Extracted String: 3oi  smcs =ipquess valu=-1n023":0-dmet","pw":"AI2025{m3m0r1z3d_mask_a1_i3_co0l}
```
