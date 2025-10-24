import numpy as np

embeddings = np.load('challenge_embeddings.npy')

flag = ""
for n in [11, 9, 12, 8, 1, 16, 18, 5, 13, 3, 21, 17, 4, 19, 10, 7, 15, 0, 20, 14, 2, 6]:
    flag += chr(embeddings[n][25].round(0).astype(int))

print(flag)
