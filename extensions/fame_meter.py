from streams import FameEvent
from time import time

fame_meter_data={
    "total_fame": 0,
    "start_time": time()
}

@FameEvent.add_hook
def fame_meter(fame_event):
    '''
    This is mainly a PoC
    It doesn't diferentiate between fame types
    '''
    # print(fame_event)
    fame_meter_data["total_fame"] += fame_event[1]["fame_gained"]
    time_delta = time() - fame_meter_data["start_time"]
    fame_per_sec = fame_meter_data["total_fame"] / time_delta
    kfame_per_h = fame_per_sec * 60*60 / 1000

    print(
        "Avg Fame (k/h):", round(kfame_per_h, 1), " |  Total:",
        f"{round(fame_meter_data['total_fame'] / 1_000, 1)}k / {round(time_delta / 60, 1)}m",
    )
