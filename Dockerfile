# Use an official Python runtime as a parent image
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Create a group and user
RUN addgroup --system appgroup && adduser --system --group appuser

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install build dependencies required for compiling packages like pytsk3 and curl for health checks
# Also install USB support and device communication libraries for phone recovery
RUN apt-get update && apt-get install -y \
    build-essential \
    libtsk-dev \
    libsqlite3-dev \
    zlib1g-dev \
    curl \
    libusb-1.0-0-dev \
    udev \
    android-tools-adb \
    p7zip-full \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY backend/requirements.txt /app/

# Install any needed packages specified in requirements.txt
# We add --no-cache-dir to reduce layer size
RUN pip install --no-cache-dir -r requirements.txt

# Setup USB device rules for phone recovery
RUN echo 'ACTION=="add", SUBSYSTEM=="usb", MODE="0666"' > /etc/udev/rules.d/99-usb.rules

# Create directories for phone recovery
RUN mkdir -p /tmp/phone_recovery /tmp/recovery_output /tmp/recovery_uploads

# Remove build dependencies to reduce image size (optional but recommended for production)
# Keeping runtime libs for TSK and USB
RUN apt-get update && apt-get remove -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy the rest of the backend application's code into the container at /app
COPY backend/ /app/backend/
COPY tests/ /app/tests/
COPY pytest.ini /app/

# Change ownership of the app directory and recovery directories to the new user
RUN chown -R appuser:appgroup /app /opt/venv /tmp/phone_recovery /tmp/recovery_output /tmp/recovery_uploads

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variable for the application port
ENV PORT 8001

# Switch to non-root user
USER appuser

# Run uvicorn when the container launches
# Use --host 0.0.0.0 to allow connections from outside the container
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]
