import os
import sys

# Add the app directory to the python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app object and rename it to application
# This is required by Phusion Passenger
from app import app as application
