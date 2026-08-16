import os
os.environ['LANGFUSE_ENABLED'] = 'false'

from langfuse.decorators import observe

@observe()
def test():
    return 'ok'

result = test()
print(f"Result: {result}")
print("Langfuse disabled test passed")