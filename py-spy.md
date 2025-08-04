Step-by-Step: Using py-spy in AKS
🧩 Prerequisites

    Your FastAPI app must be running in a Linux-based container.

    The container must include proc filesystem access (default for most containers).

    You need the ability to exec into the pod/container.

✅ Step 1: Install py-spy into the Container
Option A: Inject at Build Time (Recommended for Staging)

In your Dockerfile, add:

RUN curl -sSL https://github.com/benfred/py-spy/releases/latest/download/py-spy-linux-x86_64 -o /usr/local/bin/py-spy && \
    chmod +x /usr/local/bin/py-spy

Option B: Temporary Install in Running Pod (for Prod Debugging)

kubectl exec -it <your-pod-name> -- /bin/sh

# Inside container:
wget https://github.com/benfred/py-spy/releases/latest/download/py-spy-linux-x86_64 -O /usr/local/bin/py-spy
chmod +x /usr/local/bin/py-spy

✅ Step 2: Find the PID of the Python Process

ps aux | grep python

Example output:

root         1  0.0  0.1  ... uvicorn app.main:app

Usually the main Python process will be PID 1 inside the container.
✅ Step 3: Start Profiling (Live or Flamegraph)
🔹 Option 1: Live CPU Usage View

py-spy top --pid 1

This gives you a real-time, top-like view showing which functions consume the most CPU.
🔹 Option 2: Generate a Flamegraph

py-spy record -o /tmp/profile.svg --pid 1 --duration 60

    Captures 60 seconds of CPU profiling data

    Outputs an SVG flamegraph at /tmp/profile.svg

Then, copy it out of the container:

kubectl cp <pod-name>:/tmp/profile.svg ./profile.svg

Open it in your browser.
✅ Step 4: Stop the Profiler

    py-spy record will exit automatically after the duration you specify.

    py-spy top can be stopped with Ctrl+C.

📊 Analyze Results

    Flame graphs show the call stack and CPU time visually.

    You’ll be able to identify functions or loops that consume the most CPU.

    Can help detect inefficient loops, blocking I/O, or deep recursive calls.
