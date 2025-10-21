import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# --- Configuration ---
CSV_FILE = 'drone_telemetry.csv'
OUTPUT_DIRECTORY = 'drone_flight_paths'

print(f"--- [START] Drone Path Plotter ---")
print(f"This script will generate a separate flight path plot for *every* drone.")

# --- Step 1: Create Output Directory ---
try:
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
        print(f"Created directory: '{OUTPUT_DIRECTORY}'")
    else:
        print(f"Output directory already exists: '{OUTPUT_DIRECTORY}'")
except Exception as e:
    print(f"Error creating directory: {e}")
    sys.exit(1)

# --- Step 2: Load Data ---
print(f"\n[Step 2] Loading telemetry data from '{CSV_FILE}'...")
try:
    df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    print(f"Error: File not found: '{CSV_FILE}'")
    print("Please make sure the script is in the same directory as the CSV file.")
    sys.exit(1)

# Convert Timestamp column to datetime objects for proper sorting
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
print(f"Successfully loaded {len(df)} telemetry records.")

# --- Step 3: Get All Unique Drone IDs ---
drone_ids = df['DroneID'].unique()
print(f"\n[Step 3] Found {len(drone_ids)} unique drones. Generating plots...")

# --- Step 4: Iterate and Plot Each Drone ---
for drone_id in drone_ids:
    print(f"  - Processing {drone_id}...")
    
    # Filter for this specific drone's data and sort by time
    drone_data = df[df['DroneID'] == drone_id].sort_values(by='Timestamp')
    
    if drone_data.empty:
        print(f"    - Warning: No data found for {drone_id}. Skipping.")
        continue
    
    # Create a new plot for this drone
    plt.figure(figsize=(9, 7))
    
    # Plot Latitude vs. Longitude
    plt.plot(drone_data['Longitude'], 
             drone_data['Latitude'], 
             marker='.',       # Use a small marker for each point
             markersize=2,       # Make the marker size small
             linestyle='-',    # Connect the points with a line
             linewidth=0.5)     # Make the line thin
    
    # Add Start and End points for clarity
    # Start point
    plt.plot(drone_data['Longitude'].iloc[0], 
             drone_data['Latitude'].iloc[0], 
             'go',  # green 'o'
             markersize=8, 
             label='Start')
    # End point
    plt.plot(drone_data['Longitude'].iloc[-1], 
             drone_data['Latitude'].iloc[-1], 
             'rs',  # red square
             markersize=8, 
             label='End')
    
    plt.title(f'Full Flight Path for {drone_id}')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.legend()
    # Use 'equal' axis scaling to make the path's shape accurate
    plt.axis('equal')  
    
    # Define the save path
    plot_filename = os.path.join(OUTPUT_DIRECTORY, f'flight_path_{drone_id}.png')
    
    # Save the figure
    try:
        plt.savefig(plot_filename)
    except Exception as e:
        print(f"    - Error saving plot for {drone_id}: {e}")
    
    # Close the plot to free up memory (crucial when generating many plots)
    plt.close()

print(f"\n[Step 4] --- Plot generation complete! ---")
print(f"All {len(drone_ids)} plots have been saved to the '{OUTPUT_DIRECTORY}' folder.")
print("\n--- [COMPLETE] ---")