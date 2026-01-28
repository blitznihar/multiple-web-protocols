"""
Docstring for rest.__main__
"""

import uvicorn


def main():
    """
    Docstring for main
    """
    print("Starting REST API server...")

    uvicorn.run("rest.app:app", host="0.0.0.0", port=8060, reload=True)


if __name__ == "__main__":
    main()
