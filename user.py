import numpy as np
class User():
    def __init__(self, id: int, traffic_type: str, priority_level: int, user_delay: int):
        self.delay = self.current_delay = user_delay
        self.id = id
        self.traffic_type = traffic_type
        self.priority_level = priority_level
        self.throughput = 0
        self.rac = 0  # Resource allocation demand (RAC)
        self.average_throughput = 0  # Initialize average throughput
        self.allocated_rbs = 0
        self.total_rbs = 0
        self.instantaneous_rate = 1
        self.InitRac = 0
        self.queue_delay = 0  


    def generate_channel_quality(self) -> float:
        """Randomly generate initial channel quality for users."""
        return np.random.uniform(0.1, 1.0)

    def generate_rac(self) -> float:
        """Generate the resource allocation demand based on traffic type."""
        match self.traffic_type:
            case "video_streaming":
                return np.random.uniform(3000, 11000)  # High, constant bandwidth requirement
            case "web_browsing":    
                return np.random.exponential(1000) if np.random.rand() < 0.2 else 0  # Sporadic bursts
            case "voice_call":
                return np.random.uniform(100, 200)  # Constant, low bandwidth requirement
            case _:
                raise ValueError(f"Invalid traffic type: {self.traffic_type}")

    def minimumRBS(self):

        match self.traffic_type:
            case "video_streaming":
                return 20
            case "web_browsing":
                return 5
            case "voice_call":
                return 2