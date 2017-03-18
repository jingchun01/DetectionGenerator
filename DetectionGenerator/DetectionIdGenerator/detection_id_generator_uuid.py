import uuid
from detection_id_generator import DetectionIdGenerator


class DetectionIdGeneratorUUID(DetectionIdGenerator):
    def __init__(self):
        super(DetectionIdGeneratorUUID, self).__init__()

    def generate(self):
        return str(uuid.uuid4())
