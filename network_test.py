
import requests

# The same URL we tested with curl
url = "https://api.telegram.org/bot8208040651:AAG9a5tZKNO5dgsTDPjMJXrWlnPOLpgNPSo/getMe"

print(f"--- Attempting to connect to: {url} ---")

try:
    # Make the request with a timeout of 15 seconds
    response = requests.get(url, timeout=15)

    # Check if the request was successful
    response.raise_for_status()  # This will raise an exception for non-2xx status codes

    # If successful, print the result
    print("\n--- [SUCCESS] Connection successful! ---")
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(response.json())

except requests.exceptions.RequestException as e:
    # If any error occurs during the request, print it
    print(f"\n--- [FAILURE] An error occurred ---")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Details: {e}")
