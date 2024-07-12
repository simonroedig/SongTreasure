#Change a few things in the df:
import pandas as pd

# Read the original DataFrame
df = pd.read_csv('random_songs.csv')

# Original mappings
key_conversion = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
mode_conversion = {"Major": 1, "Minor": 0}
time_signature_conversion = {"3/4": 3, "4/4": 4, "5/4": 5, "6/4": 6, "7/4": 7}

# Reverse mappings
reverse_key_conversion = {v: k for k, v in key_conversion.items()}
reverse_mode_conversion = {v: k for k, v in mode_conversion.items()}
reverse_time_signature_conversion = {v: k for k, v in time_signature_conversion.items()}

# Apply reverse mappings
df['key'] = df['key'].map(reverse_key_conversion)
df['mode'] = df['mode'].map(reverse_mode_conversion)
df['time_signature'] = df['time_signature'].map(reverse_time_signature_conversion)

# Change id to track_id
df.rename(columns={'id': 'track_id'}, inplace=True)

df.to_csv('songs.csv', index=False)
