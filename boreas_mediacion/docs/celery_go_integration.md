# How to trigger Go scripts from Celery tasks

You can trigger Go scripts from Celery tasks in Django using Python's subprocess module. Example:

```python

# Example: Replace '/app/go_api_read/datadis_api_read' with your new Go binary path if needed.
```

- Make sure the Go binary is built and available in the container (mount or copy it).
- You can also call Go scripts via HTTP/gRPC if they are exposed as services.
- Adjust the path and arguments as needed for your Go script.
