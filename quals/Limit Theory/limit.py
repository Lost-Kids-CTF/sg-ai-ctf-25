import requests
import pandas as pd
import time

endpoint = "https://limittheory.aictf.sg:5000/experiment"

result_csv_file = "results.csv"
df = pd.read_csv(result_csv_file)

def find_limit(coconut_milk, eggs, sugar):
    lo = 1
    hi = 30000
    while lo < hi:
        time.sleep(0.4)
        pandan_leaves = (lo + hi) // 2
        payload = {
            "coconut_milk": coconut_milk,
            "eggs": eggs,
            "sugar": sugar,
            "pandan_leaves": pandan_leaves
        }
        try:
            response = requests.post(endpoint, json=payload).json()
        except Exception as e:
            print(e)
            time.sleep(10)
            continue
        if response['message'] == 'PASSED':
            lo = pandan_leaves + 1
        else:
            hi = pandan_leaves
    print(f"Found limit: {lo}")
    df.loc[len(df)] = [coconut_milk, eggs, sugar, lo]


for coconut_milk in range(5, 100, 10):
    for eggs in range(5, 100, 10):
        for sugar in range(5, 100, 10):
            find_limit(coconut_milk / 10, eggs / 10, sugar / 10)
df.to_csv(result_csv_file, index=False)
