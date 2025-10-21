import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
import numpy as np
import sys

# --- Configuration ---
CSV_FILE = 'drone_telemetry.csv'
ZSCORE_THRESHOLD = 1.0  # A standard threshold for detecting outliers
FLAG_FORMAT = "AI2025{{{}}}"
CANDIDATE_DRONES = ['DRN010', 'DRN032', 'DRN055', 'DRN069', 'DRN090'] # Filter to these drones only

print("--- [START] Drone Dance of Doom CTF Solver ---")

# --- Step 1: Load Data ---
print(f"\n[Step 1] Loading telemetry data from '{CSV_FILE}'...")
try:
    df = pd.read_csv(CSV_FILE)
    df = df[df['DroneID'].isin(CANDIDATE_DRONES)]
except FileNotFoundError:
    print(f"Error: File not found: '{CSV_FILE}'")
    print("Please make sure the script is in the same directory as the CSV file.")
    sys.exit(1)

# Convert Timestamp column to datetime objects for proper sorting and filtering
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
print(f"Successfully loaded {len(df)} telemetry records.")

# --- Step 2: Detect Instability ---
print(f"\n[Step 2] Detecting instability...")
print(f"Calculating Z-score for RotorRPM for each drone.")
print(f"Instability threshold set to: Z-score > {ZSCORE_THRESHOLD}")

# Calculate the Z-score for 'RotorRPM' *within each drone's group*.
# This is crucial so we compare a drone's RPM against its own normal behavior.
# 'transform' applies the result back to the original DataFrame's shape.
df['RPM_ZScore'] = df.groupby('DroneID')['RotorRPM'].transform(
    lambda x: zscore(x, nan_policy='omit')
)

# If a drone had 0 variance (std=0), zscore returns NaN. We fill these with 0.
df['RPM_ZScore'] = df['RPM_ZScore'].fillna(0)

# Filter to find all data points that are "unstable"
unstable_points = df[df['RPM_ZScore'].abs() > ZSCORE_THRESHOLD]

if unstable_points.empty:
    print("Error: No unstable points found with the current threshold.")
    print("You may need to adjust the ZSCORE_THRESHOLD.")
    sys.exit(1)

print(f"Found {len(unstable_points)} total unstable data points across all drones.")

# --- Step 3: Find First Instability Timestamp ---
print("\n[Step 3] Finding the first moment of instability for each drone...")

# From the unstable points, group by drone and find the *minimum* (earliest) timestamp
first_instability_times = unstable_points.groupby('DroneID')['Timestamp'].min()

print("Drones that show instability and their first hijack time:")
print(first_instability_times)

# --- Step 4: Sort the Chaos ---
print("\n[Step 4] Sorting compromised drones by hijack time...")

# Sort the drones by their first instability time (the values in the Series)
sorted_drones = first_instability_times.sort_values()

print("Drones in the order they were hijacked:")
print(sorted_drones)

# --- Step 5: Decode the Skywriting (Plotting) ---
print("\n[Step 5] Generating plot to decode the skywriting...")
print("The plot will show the combined path of the hijacked drones AFTER they became unstable.")

# Set up the plot
plt.figure(figsize=(10, 7))
plt.title('Compromised Drone Flight Paths (The "Skywriting")')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)

# Iterate through the drones *in the sorted order*
for drone_id, start_time in sorted_drones.items():
    # Get all data for this specific drone
    drone_data = df[df['DroneID'] == drone_id]
    
    # Filter for data *at or after* its unique instability time
    path_data = drone_data[drone_data['Timestamp'] >= start_time].sort_values(by='Timestamp')
    
    # Plot this drone's path on the main graph
    plt.plot(path_data['Longitude'], 
             path_data['Latitude'], 
             label=f"{drone_id} (from {start_time.time()})",
             marker='o',  # Add markers to see points
             markersize=2)

plt.legend()
plot_filename = 'drone_skywriting_plot.png'
plt.savefig(plot_filename)

print(f"\nPlot saved to '{plot_filename}'.")
print(f"==> Please open '{plot_filename}' to see the secret word. <_==")