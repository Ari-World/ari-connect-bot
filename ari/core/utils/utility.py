import uuid


def generate_uuid():

    uid = uuid.uuid4()
    lobby_code = uid.hex[:8]
    return lobby_code