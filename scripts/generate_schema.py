import json
import os
import sys

# Add the project root to the python path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    print(
        "Make sure you are running this script from the project root or "
        "scripts directory."
    )
    sys.exit(1)


def generate_openapi_schema() -> None:
    """
    Generates the OpenAPI schema from the FastAPI app and saves it to docs/openapi.json.
    """
    print("Generating OpenAPI schema...")

    # Get the OpenAPI dictionary
    openapi_data = app.openapi()

    # Define output path
    output_path = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.json")
    output_path = os.path.abspath(output_path)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(openapi_data, f, indent=2)

    print(f"✅ OpenAPI schema successfully saved to: {output_path}")


if __name__ == "__main__":
    generate_openapi_schema()
