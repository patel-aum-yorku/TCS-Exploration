import boto3

# Initialize Bedrock
client = boto3.client("bedrock-runtime", region_name="us-east-1")

print("Attempting to wake up Claude...")

try:
    response = client.converse(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        messages=[{"role": "user", "content": [{"text": "Hello, Claude! Please say hi in a haiku. Complete the haiku:\n\nGentle winds whisper,"}]}],
    )
    print(f"Success! Model said: {response['output']['message']['content'][0]['text']}")

except Exception as e:
    print(f"\nERROR: {e}")
    if "AccessDenied" in str(e):
        print(">> ACTION: Go back to the Bedrock Playground in your browser and try to chat with Claude 3 Haiku manually. It might trigger a required form.")