import uuid

def generate_transaction_reference():
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"